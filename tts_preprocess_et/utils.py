# -*- coding: utf-8 -*-

import re
import unicodedata
from estnltk.vabamorf.morf import Vabamorf
from .assets import audible_symbols, audible_connecting_symbols, units, \
                genitive_postpositions, genitive_prepositions, nominative_preceeding_words,\
                abbreviations, pronounceable_acronyms, cardinal_numbers,\
                ordinal_numbers, roman_numbers, alphabet, names

synthesizer = Vabamorf()


"""
Preprocess functions
"""

def strip_combining(s):
    """
    Helper function for simplify_unicode
    """
    return u''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def simplify_unicode(sentence):
    """
    Most accented Latin characters are pronounced just the same as the base character.
    Shrink as many extended Unicode repertoire into the Estonian alphabet as possible.
    It is GOOD for machine learning to have smaller ortographic repertoire.
    It is a BAD idea if we start using any proper name dictionaries for morph analysis
      or pronunciations later on. You are warned.
    :param sentence:
    :return: str
    """
    sentence = sentence.replace("Ð", "D").replace("Þ", "Th")
    sentence = sentence.replace("ð", "d").replace("þ", "th")
    sentence = sentence.replace("ø", "ö").replace("Ø", "Ö")
    sentence = sentence.replace("ß", "ss").replace("ẞ", "Ss")
    sentence = re.sub(r'S(c|C)(h|H)', r'Š', sentence)
    sentence = re.sub(r'sch', r'š', sentence)
    sentence = re.sub(r'[ĆČ]', r'Tš', sentence)
    sentence = re.sub(r'[ćč]', r'tš', sentence)

    sentence = re.sub(r'[^A-ZÄÖÜÕŽŠa-zäöüõšž ,]+', lambda m: r'{}'.format( strip_combining(m.group(0)) ), sentence)
    return sentence

def hyphen_phone_number(match):
    country = match.group(1)
    num_start = '-'.join(match.group(2))
    num_end = '-'.join(match.group(3).replace(' ', ''))
    
    if country:
        return f'+ {"-".join(country[1:])}-{num_start}-{num_end}'
    return f'{num_start}-{num_end}'

"""
Conversion finding functions
"""

def restore_dots(text_string, text_lemma):
    restored_lemma = ""
    j = 0
    for letter in text_string:
        if j < len(text_lemma) and letter == text_lemma[j]:
            restored_lemma += letter
            j += 1
        elif letter == '.':
            restored_lemma += '.'
        else:
            if j < len(text_lemma):
                restored_lemma += text_lemma[j:]
            break
    return restored_lemma


def tag_misc(text_string, text_lemma, index, last_index, text, postag):
    # restore lemmas in abbreviation list to uppercase (lemma for 'PS' is lowercase 'ps', lemma for 'LP-l' however is 'LP')
    # comparing text_string with text_lemma should suffice
    if text_string in abbreviations and text_string.lower() == text_lemma:
        text_lemma = text.morph_analysis[index].annotations[0].lemma = text_string
    # lowercase capitalized first words in sentence/quote, otherwise abbreviation detection may fail
    elif (index == 0 or (index > 0 and text.words[index - 1].text == '"')) and text_lemma.istitle():
        text_lemma = text.morph_analysis[index].annotations[0].lemma = text_lemma.lower()
            
    stripped_lemma = text_lemma.rstrip('.')
    if text_lemma in audible_symbols or stripped_lemma in abbreviations:
        if text_lemma not in audible_connecting_symbols:
            # lühend lemmatiseerida ilma järgneva punktita
            text_lemma = text.morph_analysis[index].annotations[0].lemma = stripped_lemma
            return text_lemma, 'M'
        # symbols that are converted only between two numbers
        elif 0 < index < last_index:
            # erandjuhtumid on koolon ja miinusmärk, mida käsitleme tehtemärkidena vaid siis, kui
            # on kahe arvu vahel ja on ka eraldatud tühikutega (vastasel juhul kaetud nt 6:2 võit)
            is_applicable = True
            # ehkki miinusmärki kirjutatakse mõtte-, mitte sidekriipsuga, on sõnastikus sidekriips,
            # sest lemmatiseerimisel muutub sidekriipsuks
            if text_lemma in (':', '-'):
                text_coordinate = text.words[index].start
                if not (text.text[text_coordinate - 1] == ' ' and
                        text.text[text_coordinate + 1] == ' '):
                    is_applicable = False
            if is_applicable and (text.words[index - 1].partofspeech[0] in ('N', 'O')) \
                    and (text.words[index + 1].partofspeech[0] in ('N', 'O')):
                return text_lemma, 'M'
    
    # ne-liitelised arvu sisaldavad sõnad asetame omadussõnaliste alla
    elif postag in ('Y', 'A') and re.match(r'^\d+-?\w*ne$', text_lemma):
        return text_lemma, 'A'
    
    # aadresside, klasside jms käsitlemine, kus sõnaliigiks Y, nt Pärna 14a või 5b
    elif postag == 'Y' and re.search(r'\d+-?\w?$', text_lemma):
        return text_lemma, 'K'
    
    return text_lemma, False


def tag_numbers(text_string, postag, is_last_index):
    # 9a is N/sgn, 10a is O/sgg
    if re.search(r'\d+\-?[a]$', text_string):
        # jäta nagu on
        return text_string

    # 13/10/2011 on miljard kolmsada kümmend üks miljonit kümmend kaks tuhat üksteist
    if re.search(r'^\d+\/\d+\/\d+$', text_string):
        # jäta nagu on
        return text_string

    if re.search(r'\d+', text_string):
        # muudame lause lõpus oleva 'O' märgendi 'N'-iks (lauselõpupunkt muudab alati eelneva arvu järgarvuks);
        # käändelõppudega arvud määratakse tihti asjatult järgarvudeks
        if (postag == 'O' and '.' not in text_string and not re.search(r'\d+-?nd', text_string)) \
                or (postag == 'O' and is_last_index):
            return 'N'
        return postag

    return False


def tag_roman_numbers(text_lemma, prev_word):
    # üldiselt on parem midagi asendamata jätta kui valesti öelda (Ca->sajas aasta, MM-l->kahe tuhandendal)
    # tegelikult vaja palju pisikesi erireegleid nagu: eelneb isikunimi, järgneb 'kvartal', on AC/DC jne
    # siia minimaalne välistus, aga kahtlasi kohti on veel (IV e intravenoosne tilguti jpm)
    if re.match('^(C|CD|CV|DI|ID|DC|DIV|L|M|MI|MM|XL|XXL|XXX)$', text_lemma):
        return False

    # Rooma numbrile ärgu eelnegu araabia nr (12 V) või & (advokaadibüroo Y&I, R&D osakond)
    if re.search(r'[\d&]$', prev_word):
        return 'M'

    # erandjuhtum on 'C', mida ei tohi teisendada 'sajandaks', kui eelneb kraadimärk (Celsius)
    if text_lemma == 'C' and prev_word == '°':
        return 'M'
    
    return 'O'


"""
Convert functions
"""

def convert_digit_block(number):
    """
    Helper function for convert_number.
    Converts a group of 3 digits to words
    :param number: str
        number (int) as a string ('110')
    :return: list
    """

    number = number.lstrip('0')
    number_strings = []

    if len(number) == 3:
        number_strings.append(cardinal_numbers[number[0]] + 'sada')
        number_strings += convert_digit_block(number[1:])
    elif len(number) == 2:
        if number[0] == '1':
            if number[1] == '0':
                number_strings.append('kümme')
            else:
                number_strings.append(cardinal_numbers[number[1]] + 'teist')
        else:
            number_strings.append(cardinal_numbers[number[0]] + 'kümmend')
            number_strings += convert_digit_block(number[1:])
    elif len(number) == 1:
        number_strings.append(cardinal_numbers[number[0]])

    return number_strings

def convert_number(number, sg_nominative):
    """
    Converts a number to words by splitting it to groups of three
    :param number: str
        number as a string
    :param sg_nominative: bool
    :return: str
    """
    number_as_string = []

    # processign all parts of a number separately (for dates, times, scores, etc.). Not pronuncing such delimiters with
    # the exception of commas.
    for element in re.split(r'[ .:-]+', re.sub(',', ' koma ', number)):
        if re.match(r'\d+', element):
            if re.match('^0+', element) or len(element) > 27:  # numbers that start with 0 and numbers larger than 10^27
                # are converted as 'null null ... '
                for character in element:
                    number_as_string.append(cardinal_numbers[character])
            else:  # grouping numbers into 3 digit blocks
                element_as_string = []
                blocks = []
                index = len(element)
                while index >= 3:
                    block = element[index - 3:index]
                    blocks.insert(0, block)
                    index -= 3
                if index > 0:
                    last_block = element[:index]
                    blocks.insert(0, last_block)

                for i, block in enumerate(blocks):  # converting each block
                    if block != '000':
                        remaining_blocks = len(blocks[i:])
                        group_text = cardinal_numbers[remaining_blocks]
                        block_converted = convert_digit_block(block)
                        element_as_string += block_converted

                        # if nominative and plural 'miljon' and larger change to partitive
                        if sg_nominative and remaining_blocks >= 3 and block_converted != ['üks']:
                            group_text += 'it'
                        if remaining_blocks > 1:
                            element_as_string.append(group_text)
                # remove 'üks' and 'ükssada' from the beginning unless the number is 1
                if element_as_string[0] == 'üks' and len(element_as_string) > 1:
                    element_as_string = element_as_string[1:]
                elif element_as_string[0] == 'ükssada':
                    element_as_string[0] = 'sada'
                number_as_string += element_as_string

        elif element:
            number_as_string.append(element)

    return ' '.join(number_as_string)


def roman_to_integer(roman):
    """
    1001. implementation of "Convert a string of Roman numerals to an integer"
    Returns 0 if the syntax is not correct (VX, CCD, IIII, MVM etc)
    :param roman: str
    :return: int
    """
    value = 0
    if re.search('I{4}|X{4}|C{4}', roman): return 0
    if re.search('V{2}|L{2}|D{2}', roman): return 0
    roman = roman.replace("IV", "IIII").replace("IX", "VIIII")
    roman = roman.replace("XL", "XXXX").replace("XC", "LXXXX")
    roman = roman.replace("CD", "CCCC").replace("CM", "DCCCC")
    if re.search('I{5}|X{5}|C{5}', roman): return 0
    maxorder = 1000
    for c in roman:
        i = roman_numbers[c]
        if i > maxorder:
            return 0
        else:
            maxorder = i
            value += i
    return value

def make_ordinal(number_as_string):
    """
    Convert a number to ordinal
    :param number_as_string: str
    :return: list
    """

    parts_as_strings = number_as_string.split()
    ordinal_parts_as_strings = parts_as_strings[:-1]  # copy all but the last word

    # convert last word to ordinal
    final_part = parts_as_strings[-1]
    # if the last word ends with 'teist', 'kümmend' või 'sada'
    special_suffix = None
    if final_part.endswith('teist'):
        special_suffix = 'teist'
    elif final_part.endswith('kümmend'):
        special_suffix = 'kümmend'
    elif final_part.endswith('sada') and final_part != 'sada':
        special_suffix = 'sada'
    if special_suffix:
        final_part = final_part.partition(special_suffix)
        # declining the first part of the word
        synthesized = synthesizer.synthesize(final_part[0], 'sg g')
        if len(synthesized) > 0:
            ordinal_parts_as_strings.append(synthesized[0] + ordinal_numbers[special_suffix])
        else:
            print(number_as_string)
            ordinal_parts_as_strings = []
    # muul juhul asendame viimase osa lihtsalt vastega sõnastikust ordinal_numbers
    else:
        ordinal_parts_as_strings.append(ordinal_numbers[parts_as_strings[-1]])

    if len(ordinal_parts_as_strings) != 0:
        return ordinal_parts_as_strings
    # kui järgarvu kujule ei õnnestunud viia, siis jätame algvormi
    else:
        return parts_as_strings

def inflect(original_as_string, own_case, next_case, ordinal):
    """
    Helper function for get_string
    """
    # original_as_string: sõne, mis koosneb algvormis sõnadest (lemmadest)
    # own_case: sõna enda käändevorm
    # next_case: lauses järgmise sobiva sõnaliigiga sõna käändevorm
    # synthesizer: Vabamorfi instants
    # ordinal: True, kui tegu on järgarvuga

    # kui järgarv, siis esmalt viime selle viimase osa järgarvu kujule
    if ordinal:
        parts_as_strings = make_ordinal(original_as_string)
    else:
        # tükeldame number_as_string tühikute järgi osadeks
        parts_as_strings = original_as_string.strip().split(' ')

    # kasutame eelisjärjekorras sõna enda käänet, aga selle puudumisel järgmise sõna käänet
    is_next = False
    if own_case not in ('', '?'):
        case = own_case
    else:
        case = next_case
        is_next = True

        # järjend käänatud sõnaosadest
    inflected = []
    # defineerime erijuhud ehk rajav, olev, ilmaütlev, kaasaütlev kääne
    special_cases = ('ter', 'es', 'ab', 'kom')

    # enamasti esimesed osad ainsuse omastavasse, viimane osa käändub teisiti,
    # v.a ainsuse nim ja osastava puhul, kus ka esimesed osad samas käändes
    # NB: järgarvu puhul tuleb esimesed osad siiski omastavasse käänata
    if (case == 'sg p' or case == 'sg n') and not ordinal:
        for part in parts_as_strings[:-1]:
            synthesized = synthesizer.synthesize(part, case)
            if len(synthesized) > 0:
                inflected.append(synthesized[0])
            else:
                return original_as_string
    else:
        for part in parts_as_strings[:-1]:
            synthesized = synthesizer.synthesize(part, 'sg g')
            if len(synthesized) > 0:
                inflected.append(synthesized[0])
            else:
                return original_as_string

    if len(case.split(' ')) > 1 and case.split(' ')[1] in special_cases and is_next:
        # kui case on üks neljast erikäändest ja järgnev käändes sõna on lauses
        # olemas, siis viimane sõna vastavalt vajadusele
        # kas ainsuse või mitmuse omastavasse (kui järgmine sõna näitab käänet)
        genitive = case.split(' ')[0] + ' g'
        synthesized = synthesizer.synthesize(parts_as_strings[-1], genitive)
        if len(synthesized) > 0:
            inflected.append(synthesized[0])
        else:
            return original_as_string
    else:
        synthesized = synthesizer.synthesize(parts_as_strings[-1], case)
        if len(synthesized) > 0:
            inflected.append(re.sub('-essu', '-essi', synthesized[0]))
        else:
            return original_as_string

    inflected_as_string = ' '.join(inflected)
    return inflected_as_string

def inflect_a_quantifiable(prev_lemma, lemma, own_case, ordinal):
    """
    Helper function for get_string
    """
    # prev_lemma: märgile/ühikule eelnev lemma tekstis, nt 25% puhul on prev_lemma '25'
    # lemma: märgi/ühiku lemma, nt '%'

    if lemma in audible_symbols:
        as_string = audible_symbols[lemma]
    elif lemma in abbreviations:
        as_string = abbreviations[lemma]
    else:
        as_string = lemma

    # kui oma kääne on määratud (ja mitte ainsuse nimetav), siis kääname selle järgi
    if own_case not in ('', '?', 'sg n'):
        as_string = inflect(as_string, own_case, '', ordinal)
    # muul juhul kääname eelneva arvu järgi
    elif prev_lemma != 'üks' and prev_lemma != '1':
        as_string = inflect(as_string, 'sg p', '', ordinal)
    return as_string

def get_string(text, index, tag):
    # text: lausest tehtud Text-objekt
    # index: teisendatava sõne asukoht lauses
    # tag: sõnele määratud märgend

    ordinal = False
    ending_lemma = ''
    beginning_lemma = ''

    # võtame esimese lemma
    lemma = text.morph_analysis.lemma[index][0]

    # Rooma numbrid teisendame araabia numbriteks
    if tag == 'O' and re.match(r'^[IVXLCDM]+-?\w*$', lemma):
        ordinal = True
        # vajadusel puhastame lemma
        match = re.search(r'-?[a-z]+$', lemma)
        if match:
            ending_lemma = match.group(0)
            # escape on vajalik selleks, et vältida segadusi regex metamärkidega nagu nt +
            lemma = lemma[:-len(ending_lemma)]
            ending_lemma = ending_lemma.strip('-')
        # teisendame araabia numbriks
        as_arabic = roman_to_integer(lemma)
        if as_arabic != 0:
            lemma = str(as_arabic)
        else:
            ordinal = False
            tag = 'M'

    # vaatame sõna analüüsi - kas kääne on tuvastatud?
    own_case = text.words[index].form[0]
    next_case = ''

    is_adj_phrase = False
    # otsime järgmise sõna käänet ainult juhul, kui sõna enda kääne on määramata
    if own_case in ('', '?'):
        # kui tegu on vahemiku, mõõtmete, loeteluga (nt 16.-20. juunini või 3 x 5 meetrit), siis
        # vaatame järjest läbi sõnu, mis jäävad lauses tahapoole (kui on)
        is_list = False
        is_span = False
        # peame saama vaadata kahe sõna võrra edasi (sest järgmine sõna on kirjavahemärk/sidesõna,
        # mis ei anna vajalikku teavet)
        if index < len(text.words) - 2:
            # loetelu tuvastamiseks vaatame algteksti alates käesoleva sõna algusest
            if re.match(r'(((\d+\.?)|([IVXLCDM]+-?\w*)),?\s)+(ja|või|ja/või|ning|ega|kui)\s((\d)|([IVXLCDM]+))', text.text[text.words[index].start:]):
                is_list = True
            # vahemiku tuvastamiseks vaatame järgmise sõna kuju ja ülejärgmise sõnaliiki
            if re.match(r'^(\.?([–\-]))|kuni$', text.words[index + 1].text) \
                    and text.words[index + 2].partofspeech[0] in ('N', 'O'):
                is_span = True
            if is_list or is_span:
                # vahemike puhul võib analüüsil esimene arv jääda järgarvuks määramata,
                # seega kui teine arv on järgarv, siis käsitleme ka esimest järgarvuna,
                # v.a lause viimase sõna puhul, mis saab enamasti eksliku järgarvumärgendi
                if is_span and tag == 'N' and text.words[index + 2].partofspeech[0] == 'O' \
                        and index + 2 != len(text.words) - 1:
                    tag = 'O'
                # leiame lähima sobiva käändevormi (peab olema kujul sg/pl + vorm)
                for word in text.words[index + 1:]:
                    current_case = word.form[0]
                    if re.match(r'(sg|pl)\s\w+', current_case):
                        # kui rajav kääne, siis läheb vahemiku esimene osa seestütlevasse (nt 10.-11. juulini)
                        if is_span and current_case in ('sg ter', 'pl ter'):
                            next_case = current_case.split()[0] + ' el'
                        else:
                            next_case = current_case
                        break
                    elif word.text in '.)";\']':  # stop if the next word marks the end of the phrase somehow
                        break

        # järgmisena vaatame, kas ees või järel on käänet määrav sõna (vaatame kuni kaks sõna edasi/tagasi,
        # sest nt 'Hind tõusis 5 € peale', 'Üle 2 km on juba läbitud')
        if next_case in ('', '?'):
            if index > 0:
                prev_lemma = text.words[index - 1].lemma[0]
                if prev_lemma in genitive_prepositions:
                    own_case = 'sg g'
                    next_case = 'sg g'
                elif prev_lemma in nominative_preceeding_words:
                    own_case = 'sg n'
                    next_case = 'sg n'
            if (index < len(text.words) - 1 and text.words[index + 1].lemma[0] in genitive_postpositions) \
                    or (index > 1 and text.words[index - 2].lemma[0] in genitive_prepositions) \
                    or (index < len(text.words) - 2 and text.words[index + 2].lemma[0] in genitive_postpositions):
                own_case = 'sg g'
                next_case = 'sg g'

        # kui next_case endiselt määramata ja vaadeldav sõna pole lauses viimane, siis vaatame järgmise
        # sõna käändevormi, omadussõnalist fraasi otsime ka kaugemale vaadates
        if next_case in ('', '?') and index < len(text.words) - 1:
            distance = 1
            for word in text.words[index + 1:]:
                current_case = word.form[0]
                if re.match(r'(sg|pl)\s\w+', current_case):
                    if tag != 'O' and word.partofspeech[0] == 'A' and word.lemma[0].endswith('ne'):
                        # changed due to sometimes getting wrong number inflections 
                        next_case = word.form[0]
                        #next_case = 'sg g'
                        
                        is_adj_phrase = True
                        # print('Leidsin omadussõnalise fraasi')
                        break
                    elif distance == 1:
                        next_case = current_case
                        break
                # kui vahepeale jääb mõni teine määratud vormiga sõna (nt tegusõna), siis edasi ei vaata
                elif current_case not in ('', '?'):
                    break
                distance += 1
                if distance > 3:
                    break

        # kui ka next_case jääbki määramata, siis jätame vaikimisi ainsuse nimetavasse
        if next_case in ('', '?'):
            own_case = 'sg n'

    # kui põhiarvsõnale järgneb ainsuse osastavas sõna ja oma kääne on määramata,
    # siis jätame ainsuse nimetavasse (nt 15 aastat)
    if tag != 'O' and next_case == 'sg p':
        own_case = 'sg n'

    # kui arvu sisaldav lemma sisaldab ka muud peale numbrite-punktide (nt 20aastane),
    # siis tuleb lemma puhastada
    as_string = lemma
    if tag in ('N', 'O', 'A', 'K'):
        # otsime sõna lõpust
        match = re.search(r'[^\d.:,]+$', lemma)
        if match:
            ending_lemma = match.group(0)
            # puhastame lemma, mis läheb teisendamisele
            lemma = lemma[:-len(ending_lemma)]
            # selleks, et sõnalõppu ennast hiljem vajadusel käänata, eemaldame eest side-/mõttekriipsu (kui on)
            if len(ending_lemma) > 1:
                ending_lemma = ending_lemma.strip('-')
            # juhtudel nagu 50-ne, kus lõpus vaid ne-liide, käsitleme edasi omadussõnalisena
            if ending_lemma == 'ne':
                tag = 'A'
        # otsime sõna algusest
        match = re.search(r'^[^\d.:,]+', lemma)
        if match:
            beginning_lemma = match.group(0)
            lemma = lemma[len(beginning_lemma):]
            # eemaldame side-/mõttekriipsu vaid juhul, kui lemma on pikem kui üks,
            # vastasel juhul võib kaduma minna nt miinusmärgina mõeldud kriips arvu ees
            if len(beginning_lemma) > 1:
                beginning_lemma = beginning_lemma.strip('-')

        is_sg_nom = False
        # määrame põhiarvsõna ains. nimetava tõeväärtuse
        if tag != 'O' and (own_case == 'sg n' or next_case == 'sg n'):
            is_sg_nom = True
        # teisendame arvu sõnalisele kujule
        as_string = convert_number(lemma, is_sg_nom)

    else:
        # leiame teisenduse sõnastikust
        if tag == 'M':
            if lemma in audible_symbols:
                as_string = audible_symbols[lemma]
            elif lemma in abbreviations:
                if not (lemma == 'u' and current_case == '?'):
                    as_string = abbreviations[lemma]

    # määrame tõeväärtuse ordinal (vajalik käänamise fn-i jaoks) vastavalt märgendile
    if tag == 'O':
        ordinal = True

    # tõeväärtus selleks, et vältida sama sõna mitmekordset käänamist
    inflected = False
    # kui enne puhastasime, siis tuleb puhastatud osa tagasi oma kohale panna
    if len(beginning_lemma) > 0 or len(ending_lemma) > 0:

        if len(ending_lemma) > 0:
            # kui omadussõnaline arvsõna, siis läheb põhiosa ainsuse omastavasse käändesse (nt 50-meetrine)
            if tag == 'A':
                as_string = inflect(as_string, 'sg g', next_case, ordinal)
                # lõpuosa võtame algkujul, mitte lemmatiseerituna, et säilitada õige kääne (nt 50-meetriseid)
                ending = re.search(r'[^\d.:,]+$', text.words[index].text).group(0).strip('-')
            # muul juhul käändub põhiosa vastavalt määratud käänetele
            else:
                # vältimaks topeltkäänamist: erikäänete puhul asendame own_case omastavaga, sest
                # kui ending on olemas ja own_case määratud, siis võime eeldada, et käändelõpp on juba näidatud
                special_cases = ('ter', 'es', 'ab', 'kom')
                if own_case not in ('', '?'):
                    if len(own_case.split(' ')) > 1 and own_case.split(' ')[1] in special_cases:
                        # vastavalt kas ainsuse või mitmuse omastav
                        genitive = own_case.split(' ')[0] + ' g'
                        as_string = inflect(as_string, genitive, next_case, ordinal)
                    else:
                        as_string = inflect(as_string, own_case, next_case, ordinal)
                    inflected = True
                # järgmise sõna järgi kääname ainult siis, kui sõnalõpp ei ole kvantifitseeritav
                # või kui on tegu omadussõnalise fraasiga
                elif ending_lemma not in units or is_adj_phrase:
                    as_string = inflect(as_string, own_case, next_case, ordinal)
                    inflected = True

                # käändumatute vormide puhul jääb sõnalõpp algkujule
                if tag == 'K':
                    ending = ending_lemma
                # muul juhul tuleb sõnalõppu samuti käänata (kui sõna enda kääne määramata, siis
                # vastavalt eelnevale arvule või kui tegu omadussõnalise fraasiga, siis vastavalt next_case'ile)
                elif ending_lemma in units:
                    if is_adj_phrase:
                        ending = inflect_a_quantifiable(lemma, ending_lemma, next_case, ordinal)
                    else:
                        ending = inflect_a_quantifiable(lemma, ending_lemma, own_case, ordinal)
                else:
                    ending = inflect(ending_lemma, own_case, next_case, ordinal)

            # kui omadussõnaline ja põhiosa koosneb vaid ühest sõnast, siis kirjutame põhiosa ja lõpu kokku
            if tag == 'A' and (len(as_string.split(' ')) == 1 or ending == 'ne'):
                as_string += ending
            else:
                as_string += ' ' + ending

        if len(beginning_lemma) > 0:
            beginning = ''
            # kääname põhiosa vaid siis, kui veel pole käänatud
            if not inflected:
                as_string = inflect(as_string, own_case, next_case, ordinal)
            # käändumatute vormide puhul jääb algus algkujule
            if tag == 'K':
                beginning = beginning_lemma
            elif beginning_lemma in audible_symbols:
                if beginning_lemma == '-':
                    # erandjuhtudel, nt aadressides nagu Aia 1a-23, jääb -23 eraldi lemmaks. miinuse
                    # eksliku hääldamise vältimiseks kontrollime, mis sellele vahetult eelneb
                    beginning_loc = text.words[index].start
                    if beginning_loc == 0 or (beginning_loc > 0 and text.text[beginning_loc - 1] in (' ', '(', '"')):
                        beginning = 'miinus'
                else:
                    beginning = audible_symbols[beginning_lemma]
            else:
                beginning = beginning_lemma
            # liidame alguse õige vormi põhiosale
            as_string = beginning + ' ' + as_string

    elif (tag == 'M') and (own_case in ('', '?', 'sg n')):
        # kui tegu on kvantifitseeritava sümboliga/ühikuga, aga own_case määramata või ainsuse nimetav,
        # siis vaatame eelmist sõna (kui on), nt 1 dollar vs 11 dollarit
        if lemma in units:
            if index > 0:
                prev_postag = text.words[index - 1].partofspeech[0]
                prev_lemma = text.words[index - 1].lemma[0]
                # kui eelmine sõna on arvsõna, siis kääname vastavalt arvule
                if prev_postag in ('N', 'O'):
                    # erandjuhul, kui kuulub omadussõnafraasi, siis läheb omastavasse (nt 15 cm pikkune)
                    if is_adj_phrase:
                        own_case = 'sg g'
                    as_string = inflect_a_quantifiable(prev_lemma, lemma, own_case, ordinal)
                # kui enne ühikut esineb kaldkriips
                elif prev_lemma == '/':
                    own_case = 'sg g'
                    as_string = inflect_a_quantifiable(prev_lemma, lemma, own_case, ordinal) + ' kohta'
        # kui ei ole kvantifitseeritav, siis oma käände puudumisel lühendit/sümbolit ei kääna
        else:
            return as_string
    else:
        as_string = inflect(as_string, own_case, next_case, ordinal)
    return as_string


"""
Postprocess functions
"""

def pronounce_names(sentence):
    """
    Converts names to match more closely to their correct pronunciation.
    E.g. Jeanne d'Arc -> Žan daark
    """
    for word in synthesizer.analyze(sentence):
        word_lemma = word['analysis'][0]['lemma'].replace('’', '\'')
        if names[word_lemma]:
            sentence = sentence.replace(word_lemma, names[word_lemma].replace('\'', ''))
    return sentence


def acronyms_lowercase(acro):
    """
    Helper function to normalize_phrase.
    """
    seq = acro.group()
    if seq in pronounceable_acronyms:
        return seq.capitalize()
    else:
        return seq

def normalize_phrase(phrase):
    """
    Converts any letters to their pronunciations if needed. For example TartuNLP to Tartu-enn-ell-pee.
    Applied to continuous uppercase letters, uppercase letters after a lowercase letter, any single letters.
    :param phrase: str
    :return: str
    """
    if re.search('[A-ZÄÖÜÕŽŠ]{2}|'
                 '[a-zäöüõšž][A-ZÄÖÜÕŽŠ]([^a-zäöüõšž]|$)|'
                 '(^|[^A-ZÄÖÜÕŽŠa-zäöüõšž])[A-ZÄÖÜÕŽŠa-zäöüõšž]([^A-ZÄÖÜÕŽŠa-zäöüõšž]|$)', phrase):
        """
        Convert pronounceable uppercase sequences (3+ chars) to lowercase to avoid spelling
        """
        phrase = re.sub(r'(?<![A-ZÄÖÜÕŽŠ])([A-ZÄÖÜÕŽŠ]{3,})(?![A-ZÄÖÜÕŽŠ])', acronyms_lowercase, phrase)

        pronunciation = ""
        for i, letter in enumerate(phrase):
            if i - 1 < 0 or re.match('[^A-ZÄÖÜÕŽŠa-zäöüõšž]', phrase[i - 1]):
                previous = " "
            else:
                previous = phrase[i - 1]
            if i + 1 == len(phrase) or re.match('[^A-ZÄÖÜÕŽŠa-zäöüõšž]', phrase[i + 1]):
                upcoming = " "
            else:
                upcoming = phrase[i + 1]

            # any uppercase letters that are not just first letters of a lowercase word (separated by space or hyphen)
            # and any single lowercase letters
            if (letter.isupper() and not (previous == " " and upcoming.islower())) or (letter.islower() and previous ==
                                                                                       upcoming == " "):
                if re.search('[A-ZÄÖÜÕŽŠa-zäöüõšž]$', pronunciation):
                    pronunciation += "-"
                pronunciation += alphabet[letter.upper()]
            else:
                pronunciation += letter

        return pronunciation
    else:
        return phrase


def spell_if_needed(match):
    """
    Most simplistic approach - any letter sequence that does not contain a vowel is unpronouncable
    All single letters and consonant sequences are spelled out (converted to their pronunciations)
    For example php -> pee-haa-pee
    Exceptions are filler words such as "hmm", "mm", etc.
    :param re.match
    :return: str
    """
    seq = match.group()
    if re.search('[AEIOUÕÄÖÜaeiouõäöü]', seq) and (len(seq) > 1):
        return seq
    # if sequence contains only m and h, skip it
    elif re.match(r'^[MHmh]+$', seq):
        return seq
    else:
        pronunciation = ""
        for i, letter in enumerate(seq):
            pronunciation += alphabet[letter.upper()]
            if (i < len(seq)-1):
                pronunciation += "-"
        return pronunciation


def read_nums_if_needed(match):
    """
    Returns number read as single digits if the number is more than 5 digits,
    otherwise returns it read as one number.
    """
    seq = match.group()
    pronunciation = ""
    if len(seq) > 5:
        for i, letter in enumerate(seq):
            pronunciation += convert_number(letter, True) + ' '
    else:
        pronunciation = convert_number(seq, True)
    return pronunciation
