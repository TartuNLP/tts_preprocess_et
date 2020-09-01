# -*- coding: utf-8 -*-

import re
from estnltk import Text
from estnltk.vabamorf.morf import Vabamorf
from collections import OrderedDict
from .assets import *

synthesizer = Vabamorf()


def roman_to_integer(roman):
    """
    Converts a string of Roman numerals to an integer
    Taken from on https://www.w3resource.com/python-exercises/class-exercises/python-class-exercise-2.php
    :param roman: str
    :return: int
    """
    value = 0
    for i in range(len(roman)):
        if i > 0 and roman_numbers[roman[i]] > roman_numbers[roman[i - 1]]:
            value += roman_numbers[roman[i]] - 2 * roman_numbers[roman[i - 1]]
        else:
            value += roman_numbers[roman[i]]
    return value


def convert_digit_block(number):
    """
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
            inflected.append(synthesized[0])
        else:
            return original_as_string

    inflected_as_string = ' '.join(inflected)
    return inflected_as_string


def inflect_a_quantifiable(prev_lemma, lemma, own_case, ordinal):
    # prev_lemma: märgile/ühikule eelnev lemma tekstis, nt 25% puhul on prev_lemma '25'
    # lemma: märgi/ühiku lemma, nt '%'
    # synthesizer: Vabamorfi instants

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
    # synthesizer: Vabamorfi instants

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
            lemma = re.sub(re.escape(ending_lemma), '', lemma)
            ending_lemma = ending_lemma.strip('-')
        # teisendame araabia numbriks
        as_arabic = roman_to_integer(lemma)
        if as_arabic != 0:
            lemma = str(as_arabic)

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
            if re.match(r'(\d+\.?,?\s)+(ja|või|ning|ega)\s\d', text.text[text.words[index].start:]):
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
                        next_case = 'sg g'
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
            lemma = re.sub(re.escape(ending_lemma), '', lemma)
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
            lemma = re.sub(re.escape(beginning_lemma), '', lemma)
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
        # kui ei ole kvantifitseeritav, siis oma käände puudumisel lühendit/sümbolit ei kääna
        else:
            return as_string
    else:
        as_string = inflect(as_string, own_case, next_case, ordinal)
    return as_string


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


def post_process(sentence):
    """
    Postprocessing to normalize the sentence and convert any URLs.
    :param sentence:
    :return: str
    """
    # TODO there should be a separate URL/email processing fuction where otherwise silent characters (hyphens,
    #  underscores) are
    #  also read. Fortunately EstNLTK does not split URLs

    sentence = re.sub(r'www\.', r' VVV punkt ', sentence)
    sentence = re.sub(r'\.ee(?![A-ZÄÖÜÕŽŠa-zäöüõšž])', r' punkt EE', sentence)
    sentence = re.sub(r'https://', r' HTTPS koolon kaldkriips kaldkriips ', sentence)
    sentence = re.sub(r'http://', r' HTTP koolon kaldkriips kaldkriips ', sentence)
    sentence = re.sub(r'@', r' ätt ', sentence)
    sentence = re.sub(r'\?([A-ZÄÖÜÕŽŠa-zäöüõšž])', r' küsimärk \g<1>', sentence)
    sentence = re.sub(r'/([A-ZÄÖÜÕŽŠa-zäöüõšž])', r' kaldkriips \g<1>', sentence)
    sentence = re.sub(r'&', r' ampersand ', sentence)
    sentence = re.sub(r'#', r' trellid ', sentence)
    sentence = re.sub(r'\.([A-ZÄÖÜÕŽŠa-zäöüõšž])', r' punkt \g<1>', sentence)

    sentence = re.sub(r' +', r' ', sentence)

    sentence = normalize_phrase(sentence)
    return sentence


def convert_sentence(sentence):
    """
        Converts a sentence to input supported by Estonian text-to-speech application.
        :param sentence: str
        :return: str
        """

    # manual substitutions:
    # ... between numbers to kuni
    sentence = re.sub(r'(\d)\.\.\.(\d)', r'\g<1> kuni \g<2>', sentence)
    # add a hyphen between any number-letter sequences  # TODO should not be done in URLs
    sentence = re.sub(r'(\d)([A-ZÄÖÜÕŽŠa-zäöüõšž])', r'\g<1>-\g<2>', sentence)
    sentence = re.sub(r'([A-ZÄÖÜÕŽŠa-zäöüõšž])(\d)', r'\g<1>-\g<2>', sentence)
    # remove grouping between numbers
    sentence = re.sub(r'([0-9]) ([0-9])', r'\g<1>\g<2>', sentence)

    # Morphological analysis with estNLTK
    text = Text(sentence).analyse('morphology')

    # Dict of converable words where keys are:
    # 'N' - cardinal numbers;
    # 'O' - ordinal numbers;
    # 'M' - other (audible symbols, abbreviations, units);
    # 'A' - adjective forms vormid (eg. words with -ne/-line prefix, 10-aastane);
    # 'K' - indeclinable forms (addresses, classes where the prefix is not an abbreviation);
    # 'U' - urls and email addresses
    # TODO something for URLs
    # the value is a list of such word indexes

    tag_indices = defaultdict(lambda: [])
    num_postags = ('N', 'O')
    misc_postags = ('Z', 'Y', 'J', 'A')

    for i, postag_list in enumerate(text.morph_analysis.partofspeech):
        text_string = text.words[i].text
        text_lemma = text.words[i].lemma[0]
        postag = postag_list[0]
        last_index = len(text.words) - 1

        # restore any dots inside lemmas (they dissappear when there is more than two usually)
        if text_lemma.count('.') < text_string.count('.'):
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

            text_lemma = text.morph_analysis[i].annotations[0].lemma = restored_lemma

        # restore any audible symbols in lemmas (for example '+4' may become '4')
        if text_string[0] in audible_symbols and text_lemma[0] not in audible_symbols:
            text_lemma = text.morph_analysis[i].annotations[0].lemma = text_string[0] + text_lemma

        if postag in misc_postags:
            # lowercase capitalized first words in sentence/quote, otherwise abbreviation detection may fail
            if (i == 0 or (i > 0 and text.words[i - 1].text == '"')) and text_lemma.istitle():
                text_lemma = text.morph_analysis[i].annotations[0].lemma = text_lemma.lower()
            if text_lemma in audible_symbols or text_lemma in abbreviations:
                if text_lemma not in audible_connecting_symbols:
                    tag_indices['M'].append(i)
                    continue
                # symbols that are converted only between two numbers
                elif 0 < i < last_index:
                    # erandjuhtumid on koolon ja miinusmärk, mida käsitleme tehtemärkidena vaid siis, kui
                    # on kahe arvu vahel ja on ka eraldatud tühikutega (vastasel juhul kaetud nt 6:2 võit)
                    is_applicable = True
                    # ehkki miinusmärki kirjutatakse mõtte-, mitte sidekriipsuga, on sõnastikus sidekriips,
                    # sest lemmatiseerimisel muutub sidekriipsuks
                    if text_lemma in (':', '-'):
                        text_coordinate = text.words[i].start
                        if not (text.text[text_coordinate - 1] == ' ' and
                                text.text[text_coordinate + 1] == ' '):
                            is_applicable = False
                    if is_applicable and (text.words[i - 1].partofspeech[0] in ('N', 'O')) \
                            and (text.words[i + 1].partofspeech[0] in ('N', 'O')):
                        tag_indices['M'].append(i)
                        continue
            # ne-liitelised arvu sisaldavad sõnad asetame omadussõnaliste alla
            elif postag in ('Y', 'A') and re.match(r'^\d+-?\w*ne$', text_lemma):
                tag_indices['A'].append(i)
                continue
            # aadresside, klasside jms käsitlemine, kus sõnaliigiks Y, nt Pärna 14a või 5b
            elif postag == 'Y' and re.search(r'\d+-?\w?$', text_lemma):
                tag_indices['K'].append(i)
                continue

        elif postag in num_postags:
            if re.search(r'\d+', text_string):
                # muudame lause lõpus oleva 'O' märgendi 'N'-iks (lauselõpupunkt muudab alati eelneva arvu järgarvuks);
                # käändelõppudega arvud määratakse tihti asjatult järgarvudeks
                if (postag == 'O' and '.' not in text_string and not re.search(r'\d+-?nd', text_string)) \
                        or (postag == 'O' and i == last_index):
                    postag = 'N'
                tag_indices[postag].append(i)
                continue

        # Rooma numbrite käsitlemine (sõnaliigiks saab automaatselt 'O' või käänatuna 'Y'
        # või käändumatu lõpuga 'H')

        # vaatame lemmat ehk selle tingimuslause alla mahuvad ka õigesti käänatud ja
        # käändelõppudega juhtumid, nt VI-le, IIIks
        if postag in ('O', 'Y') and re.match('^[IVXLCDM]+$', text_lemma):
            # erandjuhtum on 'C', mida ei tohi teisendada 'sajandaks', kui eelneb kraadimärk (Celsius)
            if text_lemma == 'C' and i > 0:
                if text.words[i - 1].text != '°':
                    tag_indices['O'].append(i)
                    continue
            else:
                tag_indices['O'].append(i)
                continue
        # juhtumid nagu nt VIIa või Xb klass võivad saada kas 'Y' või 'H' märgendi;
        # lõppu lubame vaid ühe väiketähe, et vältida pärisnimede nagu
        # Mai või Ivi Rooma numbriteks arvamist
        elif postag in ('Y', 'H') and re.match('^[IVXLCDM]+[a-z]?$', text_lemma):
            tag_indices['O'].append(i)
            continue

        # capitalized abbreviations
        elif postag == 'Y':
            normalized_lemma = normalize_phrase(text_lemma)
            if normalized_lemma != text_lemma:
                text.morph_analysis[i].annotations[0].lemma = normalized_lemma
                tag_indices['Y'].append(i)
                continue

        # undetected numbers with ne/line suffix
        if re.match(r'^\d+-?[a-zA_ZäöüõÄÖÕÜšžŠŽ]+(ne|line)$', text_lemma):
            tag_indices['A'].append(i)

    # kui lauses leidub midagi, mida teisendada
    if len(tag_indices) > 0:
        # loome uue sõnastiku, kus võtmeteks paarid sõnade algus- ja lõpuindeksitest, väärtusteks sõnad teksti kujul
        location_dict = {(text.words[i].start, text.words[i].end): text.words[i].text
                         for key, value in tag_indices.items() for i in value}

        # sorteerime loodud sõnastiku elemendid (ehk võti-väärtus paarid) ja teeme OrderedDicti, mis hoiab järjestust
        location_dict = OrderedDict(sorted(location_dict.items()))

        for tag in tag_indices:
            index_list = tag_indices[tag]
            for index in index_list:
                # leiame sõna algus- ja lõpupositsioonid
                start_pos = text.words[index].start
                end_pos = text.words[index].end
                # viime sõne kujule
                in_string_form = get_string(text, index, tag)

                # asendame location_dict sõnastikus algse teksti teisendusega
                location_dict[(start_pos, end_pos)] = in_string_form

        # vaatame läbi kõik elemendid sõnastikus location_dict (järjestatud indeksite järgi lauses)
        new_sentence = ''
        for i, (key, elem) in enumerate(location_dict.items()):
            start_pos = key[0]
            end_pos = key[1]
            # kui teisendus on kohe lause alguses, siis tekitame esisuurtähe
            if start_pos == 0:
                elem = elem.capitalize()
            # kui teisendus ei ole kohe alguses, aga asub otsekõne alguses ehk vahetult
            # pärast jutumärki, siis tekitame samuti esisuurtähe
            elif text.text[start_pos - 1] == '"':
                elem = elem.capitalize()
            # kui teisenduse algus ei ole lause esimene täht, siis vaatame, kas on vaja tühik vahele lisada
            if start_pos > 0 and not re.match(r'[\s\d:;–\-_("]', text.text[start_pos - 1]):
                elem = ' ' + elem
            # kui teisenduse lõpp ei ole lause viimane täht, siis vaatame, kas on vaja tühik
            # vahele lisada (vajalik juhtudel, kus originaallauses on tühikuta, nt 5.b)
            if end_pos != len(text.text) and not re.match(r'[\s\d.,:;–\-_()!?"]', text.text[end_pos]):
                elem += ' '
            # kui tegu ei ole viimase elemendiga sõnastikus location_dict
            if i < len(location_dict.keys()) - 1:
                # leiame järgmise sõna alguse indeksi
                next_index = list(location_dict.items())[i + 1][0][0]
                # kontrollime, kas algtekstis on vaja muudatusi teha (vajalik nt vahemike puhul,
                # kus kaks teisendust on kõrvuti ja nende vahel side- või mõttekriips,
                # et eemaldada lõpptekstist kahe sõna vahelised kirjavahemärgid)
                if re.match(r'^[.\s]?[\-:]\s?$', text.text[end_pos:next_index]):
                    in_between = ' '
                # kui tegu on mõttekriipsu või kolme punktiga kahe teisenduse vahel,
                # siis asendame sõnaga 'kuni'
                elif re.match(r'^\s?[.]?–\s?$', text.text[end_pos:next_index]) or \
                        re.match(r'^\s?\.{3}\s?$', text.text[end_pos:next_index]):
                    in_between = ' kuni '
                else:
                    in_between = text.text[end_pos:next_index]
                # kui tegu on esimese elemendiga sõnastikus
                if i == 0:
                    new_sentence += text.text[:start_pos] + elem + in_between
                else:
                    new_sentence += elem + in_between
            # kui tegu on viimase elemendiga sõnastikus location_dict
            else:
                if i == 0:
                    new_sentence += text.text[:start_pos] + elem + text.text[end_pos:]
                else:
                    new_sentence += elem + text.text[end_pos:]
                # kui arv lõpeb punktiga, siis võib teisendatud
                # lause lõpust punkt kaduda
                if text.text.endswith('.') and not new_sentence.endswith('.'):
                    new_sentence += '.'
        return post_process(new_sentence)
    else:
        return post_process(sentence)
