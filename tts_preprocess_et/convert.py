# -*- coding: utf-8 -*-

import re
from estnltk import Text
from .assets import last_resort, audible_symbols, abbreviations, units, special_names
from .utils import simplify_unicode, hyphen_phone_number, \
    restore_dots, tag_misc, tag_numbers, tag_roman_numbers, \
    get_string, \
    pronounce_names, normalize_phrase, spell_if_needed, read_nums_if_needed
from collections import defaultdict, OrderedDict


def pre_process(sentence, accessibility):
    # manual substitutions:
    # ... between numbers to kuni
    sentence = re.sub(r'(\d)\.\.\.?(\d)', r'\g<1> kuni \g<2>', sentence)

    # reduce Unicode repertoire _before_ inserting any hyphens
    sentence = simplify_unicode(sentence)

    # hyphenate bank iban code
    sentence = re.sub(r'[a-zA-Z]{2}[0-9]{2}[a-zA-Z0-9]{4}[0-9]{7}([a-zA-Z0-9]?){0,16}', lambda match: '-'.join(match.group()), sentence)

    # hyphenate number from word ending e.g. DigiDoc4 -> digi-dokk-4
    sentence = re.sub(r'(^| )\"?({})((,?\"? |\.\"?)|$)'.format('|'.join(map(re.escape, special_names.keys()))), lambda match: match.group().replace(match.group(2), special_names[match.group(2)]), sentence)
    #sentence = re.sub(r'(?<![A-ZÄÖÜÕŽŠa-zäöüõšž0-9\-])([A-ZÄÖÜÕŽŠa-zäöüõšž]+)(\d+)(?![A-ZÄÖÜÕŽŠa-zäöüõšž])', r'\g<1>-\g<2>', sentence)

    # hyphenate words containing a number in the middle (mostly for letter-digit mixed codes)
    sentence = re.sub(r'(([A-ZÄÖÜÕŽŠa-zäöüõšž]+\d|\d+[A-ZÄÖÜÕŽŠa-zäöüõšž])[A-ZÄÖÜÕŽŠa-zäöüõšž0-9]*)', lambda match: ', '.join(match.group()) + ',' if len(match.group()) >= 5 else match.group(), sentence)

    # hyphenate any number-letter sequences  # TODO should not be done in URLs
    sentence = re.sub(r'(\d)([A-ZÄÖÜÕŽŠa-zäöüõšž])', r'\g<1>-\g<2>', sentence)
    sentence = re.sub(r'([A-ZÄÖÜÕŽŠa-zäöüõšž])(\d)', r'\g<1>-\g<2>', sentence)

    # hyphenate capitalized joined words
    sentence = re.sub(r'([a-zäöüõšž])([A-ZÄÖÜÕŽŠ][a-zäöüõšž]*)', lambda match: f'{match.group(1)}-{match.group(2)}' if not match.group() in abbreviations else match.group(), sentence)

    # separate + and add hyphen between every digit in phone number
    sentence = re.sub(r'(\+\d{3})? (\d{3}) (\d{4,5}|(\d{2} \d{2}))', hyphen_phone_number, sentence)
    
    # remove grouping between numbers
    # keeping space in 2006-10-27 12:48:50, in general require group of 3
    sentence = re.sub(r'(?<![0-9\-])([0-9]{1,3}) ([0-9]{3})(?!\d)', r'\g<1>\g<2>', sentence)

    sentence = re.sub(r'(\d) (\d)', r'\g<1>-\g<2>', sentence)

    if accessibility:
        sentence = re.sub(r'((?<=[^A-ZÄÖÜÕŽŠa-zäöüõšž])|^)( ?)([A-ZÄÖÜÕŽŠ])(?=([^A-ZÄÖÜÕŽŠa-zäöüõšž]|$))', lambda match: match.group(2) + 'suur-täht-' + match.group(3).lower(), sentence)

    return sentence


def find_conversions(sentence):
    # Morphological analysis with estNLTK
    text = Text(sentence).tag_layer('morph_analysis')

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
        # morph considers the sentence period to be a part of the lemma if unsure (eg €.). Avoid that
        if text_lemma.count('.') < text_string.count('.') and (i < last_index or text_lemma not in audible_symbols):
            text_lemma = text.morph_analysis[i].annotations[0].lemma = restore_dots(text_string, text_lemma)
        

        # restore any audible symbols in lemmas (for example '+4' may become '4')
        if text_string[0] in audible_symbols and text_lemma[0] not in audible_symbols:
            text_lemma = text.morph_analysis[i].annotations[0].lemma = text_string[0] + text_lemma
        

        if postag in misc_postags:
            text_lemma, tag = tag_misc(text_string, text_lemma, i, last_index, text, postag)
            if tag:
                tag_indices[tag].append(i)
                continue

        elif postag in num_postags:
            tag = tag_numbers(text_string, postag, i == last_index)
            if tag:
                if len(tag) > 1:
                    text.morph_analysis[i].annotations[0].lemma = tag
                else:
                    tag_indices[tag].append(i)
                continue
        

        # Rooma numbrite käsitlemine (sõnaliigiks saab automaatselt 'O' või käänatuna 'Y'
        # või käändumatu lõpuga 'H')

        # vaatame lemmat ehk selle tingimuslause alla mahuvad ka õigesti käänatud ja
        # käändelõppudega juhtumid, nt VI-le, IIIks
        # lisaks ei tohiks rooma numbrile järgneda araabia number
        if postag in ('O', 'Y') and re.match('^[IVXLCDM]+$', text_lemma) and (len(text.morph_analysis.partofspeech) == i+1 or not text.morph_analysis.partofspeech[i+1][0] in num_postags):
            tag = tag_roman_numbers(text_lemma, '' if i == 0 else text.words[i - 1].text)
            if tag:
                tag_indices[tag].append(i)
            continue
        
        # juhtumid nagu nt VIIa või Xb klass võivad saada kas 'Y' või 'H' märgendi;
        # lõppu lubame vaid ühe väiketähe, et vältida pärisnimede nagu
        # Mai või Ivi Rooma numbriteks arvamist
        # edit: selle malliga sobivad ainult väikesed numbrid
        elif postag in ('Y', 'H') and re.match('^[IVX]+[a-z]?$', text_lemma):
            tag_indices['O'].append(i)
            continue

        # capitalized abbreviations
        elif postag == 'Y':
            normalized_lemma = normalize_phrase(text_lemma)
            if normalized_lemma != text_lemma:
                text.morph_analysis[i].annotations[0].lemma = normalized_lemma
                # lisaks peame käändega ettevaatlik olema, et käändelõputa Y ei ühilduks järgnevaga
                if text.morph_analysis[i].annotations[0].form != '?':
                    tag_indices['Y'].append(i)
                continue
        

        # undetected numbers with ne/line suffix
        if re.match(r'^\d+-?[a-zA_ZäöüõÄÖÕÜšžŠŽ]+(ne|line)$', text_lemma):
            tag_indices['A'].append(i)
    
    return text, tag_indices


def create_conversion_location_dict(text, conversions):
    # loome uue sõnastiku, kus võtmeteks paarid sõnade algus- ja lõpuindeksitest, väärtusteks sõnad teksti kujul
    location_dict = {(text.words[i].start, text.words[i].end): text.words[i].text
                        for key, value in conversions.items() for i in value}

    # sorteerime loodud sõnastiku elemendid (ehk võti-väärtus paarid) ja teeme OrderedDicti, mis hoiab järjestust
    location_dict = OrderedDict(sorted(location_dict.items()))

    for tag in conversions:
        index_list = conversions[tag]
        for index in index_list:
            # leiame sõna algus- ja lõpupositsioonid
            start_pos = text.words[index].start
            end_pos = text.words[index].end
            # viime sõne kujule
            in_string_form = get_string(text, index, tag)

            # asendame location_dict sõnastikus algse teksti teisendusega
            location_dict[(start_pos, end_pos)] = in_string_form
    
    return location_dict

def sentence_part_conversion(index, start_pos, end_pos, elem, text, location_dict):
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
    if index < len(location_dict.keys()) - 1:
        # leiame järgmise sõna alguse indeksi
        next_index_start, next_index_end = list(location_dict.items())[index + 1][0]
        # kontrollime, kas algtekstis on vaja muudatusi teha (vajalik nt vahemike puhul,
        # kus kaks teisendust on kõrvuti ja nende vahel side- või mõttekriips,
        # et eemaldada lõpptekstist kahe sõna vahelised kirjavahemärgid)
        if re.match(r'^[.\s]?[\-:]\s?$', text.text[end_pos:next_index_start]):
            in_between = ' '
        # kui tegu on mõttekriipsu või kolme punktiga kahe teisenduse vahel,
        # siis asendame sõnaga 'kuni'
        elif re.match(r'^\s?[.]?–\s?$', text.text[end_pos:next_index_start]) or \
                re.match(r'^\s?\.{3}\s?$', text.text[end_pos:next_index_start]):
            in_between = ' kuni '
        else:
            in_between = text.text[end_pos:next_index_start]
        
        # kui kaldkriips esineb enne ühikut
        if in_between.endswith('/') and text.text[next_index_start:next_index_end] in units:
            in_between = in_between[:-1]

        # kui tegu on esimese elemendiga sõnastikus
        if index == 0:
            return text.text[:start_pos] + elem + in_between
        return elem + in_between
    # kui tegu on viimase elemendiga sõnastikus location_dict
    else:
        if index == 0:
            return text.text[:start_pos] + elem + text.text[end_pos:]
        return elem + text.text[end_pos:]

def apply_conversions(text, conversions):
    location_dict = create_conversion_location_dict(text, conversions)

    # vaatame läbi kõik elemendid sõnastikus location_dict (järjestatud indeksite järgi lauses)
    new_sentence = ''
    for i, (key, elem) in enumerate(location_dict.items()):
        new_sentence += sentence_part_conversion(i, key[0], key[1], elem, text, location_dict)
    
    # kui arv lõpeb punktiga, siis võib teisendatud
    # lause lõpust punkt kaduda
    if text.text.endswith('.') and not new_sentence.endswith('.'):
        new_sentence += '.'
    return new_sentence


def post_process(sentence, accessibility):
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

    #lauselõpumärgid
    if accessibility:
        sentence = sentence.replace('?', ' küsimärk ')
        sentence = sentence.replace('!', ' hüüumärk ')
    else:
        sentence = re.sub(r'\?([A-ZÄÖÜÕŽŠa-zäöüõšž])', r' küsimärk \g<1>', sentence)
    sentence = re.sub(r',(\.?)$', r'\g<1>', sentence)
    sentence = re.sub(r'\.([A-ZÄÖÜÕŽŠa-zäöüõšž])', r' punkt \g<1>', sentence)

    #sulud
    sentence = re.sub(r' ?(\(|\[|\{)', r',\g<1>', sentence) # pausi tekitamiseks enne sulge
    if accessibility:
        sentence = re.sub(r'(\)|\]|\}),? ', ', sulu lõpp,', sentence) # loeb sulu lõpu ja tekitab pausi peale sulge
        sentence = re.sub(r'(\)|\]|\})([.!?]?)$', r', sulu lõpp\g<2>', sentence) # loeb sulu lõpu lause lõpus
    else:
        sentence = re.sub(r'(\)|\]|\}),? ', ', ', sentence) # kaotab sulu lõpu ja tekitab pausi peale sulge
        sentence = re.sub(r'(\)|\]|\})([.!?]?)$', r'\g<2>', sentence) # kaotab sulu lõpu lause lõpus
    
    sentence = re.sub(r' +', r' ', sentence)

    # temporarily remove whitespace around last resort symbols
    # replace annoying long repetitions with ' repeating symbol X ',
    # then any remaining symbols (in URLs etc) that look like audible
    for key in last_resort:
        escaped_key = re.escape(key)
        sentence = re.sub(r' ?{} ?'.format(escaped_key), r'{}'.format(escaped_key), sentence)
        korduv = escaped_key + '{4,}'
        sentence = re.sub(r'{}'.format(korduv), r" korduv märk{}".format(last_resort[key]), sentence)
    sentence = sentence.translate( str.maketrans(last_resort) )
    sentence = sentence.replace('\\', '')

    sentence = pronounce_names(sentence)

    # very long uppercase sequences are probably words
    sentence = re.sub(r'[A-ZÄÖÜÕŽŠ,\-]{5,}', lambda m: r'{}'.format(m.group(0).lower()), sentence)

    sentence = normalize_phrase(sentence)
    """
    Convert unpronounceable letter sequences to spelled form
    Convert all remaining numeric sequences to words in sg. nom
    """
    sentence = re.sub(r'[A-ZÄÖÜÕŽŠa-zäöüõšž]{2,}', spell_if_needed, sentence)
    sentence = re.sub(r'\d+', read_nums_if_needed, sentence)

    return sentence


def convert_sentence(sentence, accessibility=False):
    """
        Converts a sentence to input supported by Estonian text-to-speech application.
        :param sentence: str
        :return: str

        #TODO
        :param accessibility: bool
        """
    
    sentence = pre_process(sentence, accessibility)

    # Otsib, kas midagi tuleb teisendada
    text, conversions = find_conversions(sentence)

    # kui lauses leiti midagi, mida teisendada
    if len(conversions) > 0:
        sentence = apply_conversions(text, conversions)
    
    return post_process(sentence, accessibility)
