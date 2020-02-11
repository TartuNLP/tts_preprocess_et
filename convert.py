# -*- coding: utf-8 -*-


import re
from estnltk import Text
from estnltk.vabamorf.morf import Vabamorf
from collections import defaultdict
from collections import OrderedDict

voc_symbol_dict = {'@': 'ät', '$': 'dollar', '%': 'protsent', '&': 'ja', '+': 'pluss',
                   '=': 'võrdub', '€': 'euro', '£': 'nael', '§': 'paragrahv', '°': 'kraad',
                   '±': 'pluss miinus', '‰': 'promill', '×': 'korda', 'x': 'korda',
                   '*': 'korda', '∙': 'korda', ':': 'jagada', '-': 'miinus'}

# sümbolid, mis häälduvad vaid siis, kui asuvad kahe arvu vahel
in_betweens = ('×', 'x', '*', ':', '-')

# sümbolid ja lühendid, mis käänduvad vastavalt eelnevale arvule (nt 1 meeter vs 5 meetrit)
quantifiables = ('$', '%', '‰', '€', '£', '°', 'a', 'atm', 'km', 'km²', 'm', 'm²', 'm³', 'mbar', 'cm',
                 'ct', 'd', 'dB', 'eks', 'h', 'ha', 'hj', 'hl', 'mm', 'tk', 'p', 'rbl', 'rm', 'lk',
                 'pk', 's', 'sl', 'spl', 'sek', 'tk', 'tl', 'kr', 'min', 't', 'mln', 'mld', 'mg',
                 'g', 'kg', 'ml', 'l', 'cl', 'dl')

# kaassõnad, mille korral eelnev või järgnev arvsõna läheb omastavasse käändesse
pre_gens = ('üle', 'alla')
post_gens = ('võrra', 'ümber', 'pealt', 'peale', 'ringis', 'paiku', 'aegu', 'eest')
# sõnad, mille korral järgnev arvsõna läheb nimetavasse käändesse (kui oma kääne määramata)
pre_noms = ('kell', 'number', 'aasta', 'kl', 'nr', 'a')

abbrev_dict = defaultdict(None,
                          {'a': 'aasta',
                           'aa': 'arveldusaasta',
                           'adm': 'admiral',
                           'aj': 'ajutine',
                           'ak': 'arvelduskonto',
                           'akad': 'akadeemik',
                           'al': 'alates',
                           'apr': 'aprill',
                           'atm': 'atmosfäär',
                           'aug': 'august',
                           'aü': 'ametiühing',
                           'bulg': 'bulgaaria keeles',
                           'ca': 'umbes',
                           'cl': 'sentiliiter',
                           'cm': 'sentimeeter',
                           'ct': 'karaat',
                           'dB': 'detsibell',
                           'dal': 'dekaliiter',
                           'dets': 'detsember',
                           'dipl': 'diplom',
                           'dir': 'direktor',
                           'dl': 'detsiliiter',
                           'dots': 'dotsent',
                           'dr': 'doktor',
                           'e': 'ehk',
                           'e.m.a': 'enne meie ajaarvamist',
                           'eKr': 'enne Kristuse sündi',
                           'eks': 'eksemplar',
                           'end': 'endine',
                           'g': 'gramm',
                           'h': 'tund',
                           'ha': 'hektar',
                           'hbr': 'heebrea keeles',
                           'hisp': 'hispaania keeles',
                           'hj': 'hobujõud',
                           'hl': 'hektoliiter',
                           'hn': 'hiina keeles',
                           'hr': 'härra',
                           'hrl': 'harilikult',
                           'ik': 'isikukood',
                           'ingl': 'inglise keeles',
                           'ins': 'insener',
                           'it': 'itaalia keeles',
                           'j': 'jõgi',
                           'j.a': 'juures asuv',
                           'jaan': 'jaanuar',
                           'jj': 'ja järgmine',
                           'jm': 'ja muud',
                           'jms': 'ja muud sellised',
                           'jmt': 'ja mitmed teised',
                           'jn': 'joonis',
                           'jne': 'ja nii edasi',
                           'jpn': 'jaapani keeles',
                           'jpt': 'ja paljud teised',
                           'jr': 'juunior',
                           'jrk': 'järjekord',
                           'jsk': 'jaoskond',
                           'jt': 'ja teised',
                           'juh': 'juhataja',
                           'jun': 'juunior',
                           'jv': 'järv',
                           'k': 'keel',
                           'k.a': 'kaasa arvatud',
                           'kcal': 'kilokalor',
                           'kd': 'köide',
                           'kg': 'kilogramm',
                           'khk': 'kihelkond',
                           'kin': 'kindral',
                           'kin-ltn': 'kindralleitnant',
                           'kin-mjr': 'kindralmajor',
                           'kk': 'keskkool',
                           'kl': 'kell',
                           'klh': 'kolhoos',
                           'km': 'kilomeeter',
                           'km/h': 'kilomeetrit tunnis',
                           'km²': 'ruutkilomeeter',
                           'knd': 'kandidaat',
                           'kod': 'kodanik',
                           'kol': 'kolonel',
                           'kol-ltn': 'kolonelleitnant',
                           'kop': 'kopikas',
                           'kpl': 'kauplus',
                           'kpt': 'kapten',
                           'kpt-ltn': 'kaptenleitnant',
                           'kpt-mjr': 'kaptenmajor',
                           'kr': 'kroon',
                           'krt': 'korter',
                           'kt': 'kohusetäitja',
                           'kub': 'kubermang',
                           'kv': 'kvartal',
                           'l': 'liiter',
                           'ld': 'ladina keeles',
                           'lg': 'lõige',
                           'lj': 'linnajagu',
                           'lk': 'lehekülg',
                           'lm': 'liidumaa',
                           'lo': 'linnaosa',
                           'lp': 'lugupeetud',
                           'lpn': 'lipnik',
                           'ltn': 'leitnant',
                           'lüh': 'lühend',
                           'm': 'meeter',
                           'm.a.j': 'meie ajaarvamise järgi',
                           'm/s': 'meetrit sekundis',
                           'mag': 'magister',
                           'mbar': 'millibaar',
                           'mg': 'milligramm',
                           'mh': 'muu hulgas',
                           'min': 'minut',
                           'mjr': 'major',
                           'mk': 'maakond',
                           'ml': 'milliliiter',
                           'mld': 'miljard',
                           'mln': 'miljon',
                           'mm': 'millimeeter',
                           'mnt': 'maantee',
                           'mob': 'mobiiltelefon',
                           'ms': 'muuseas',
                           'm²': 'ruutmeeter',
                           'm³': 'kuupmeeter',
                           'n': 'neiu',
                           'n-srs': 'nooremseersant',
                           'n-vbl': 'nooremveebel',
                           'n-ö': 'nii-öelda',
                           'nim': 'nimeline',
                           'nn': 'niinimetatud',
                           'nov': 'november',
                           'nr': 'number',
                           'nt': 'näiteks',
                           'näd': 'nädal',
                           'okt': 'oktoober',
                           'osk': 'osakond',
                           'p': 'punkt',
                           'p.o': 'peab olema',
                           'pKr': 'pärast Kristuse sündi',
                           'pa': 'poolaasta',
                           'pk': 'postkast',
                           'pl': 'plats',
                           'pms': 'peamiselt',
                           'port': 'portugali keeles',
                           'pr': 'proua',
                           'prl': 'preili',
                           'prof': 'professor',
                           'ps': 'poolsaar',
                           'pst': 'puiestee',
                           'ptk': 'peatükk',
                           'raj': 'rajoon',
                           'rbl': 'rubla',
                           'reg-nr': 'registreerimisnumber',
                           'rg-kood': 'registrikood',
                           'rk': 'raamatukogu',
                           'rkl': 'riigikoguliige',
                           'rm': 'ruumimeeter',
                           'rms': 'reamees',
                           'rmtk': 'raamatukogu',
                           'rmtp': 'raamatupidamine',
                           'rtj': 'raudteejaam',
                           'rts': 'rootsi keeles',
                           'rum': 'rumeenia keeles',
                           's': 'sekund',
                           's.a': 'sel aastal',
                           's.o': 'see on',
                           's.t': 'see tähendab',
                           'saj': 'sajand',
                           'sealh': 'sealhulgas',
                           'seals': 'sealsamas',
                           'sek': 'sekund',
                           'sen': 'seenior',
                           'sept': 'september',
                           'sh': 'sealhulgas',
                           'skp': 'selle kuu päeval',
                           'sks': 'saksa keeles',
                           'sl': 'supilusikatäis',
                           'sm': 'seltsimees',
                           'snd': 'sündinud',
                           'spl': 'supilusikatäis',
                           'srn': 'surnud',
                           'srs': 'seersant',
                           'st': 'see tähendab',
                           'std': 'staadion',
                           'stj': 'saatja',
                           'surn': 'surnud',
                           'sü': 'säilitusüksus',
                           'sünd': 'sündinud',
                           't': 'tund',
                           'tehn': 'tehniline',
                           'tel': 'telefon',
                           'tk': 'tükk',
                           'tl': 'teelusikatäis',
                           'tlk': 'tõlkija',
                           'tn': 'tänav',
                           'tr': 'trükk',
                           'ts': 'tsentner',
                           'tv': 'televisioon',
                           'u': 'umbes',
                           'ukj': 'uue, Gregoriuse kalendri järgi',
                           'ukr': 'ukraina keeles',
                           'ung': 'ungari keeles',
                           'v': 'vald',
                           'v-ltn': 'vanemleitnant',
                           'v-mdr': 'vanemmadrus',
                           'v-vbl': 'vanemveebel',
                           'v.a': 'välja arvatud',
                           'van': 'vananenud',
                           'vbl': 'veebel',
                           'veebr': 'veebruar',
                           'vkj': 'vana, Juliuse kalendri järgi',
                           'vkr': 'vanakreeka keeles',
                           'vm': 'või muud',
                           'vms': 'või muud sellist',
                           'vrd': 'võrdle',
                           'vt': 'vaata',
                           'õa': 'õppeaasta',
                           'õp': 'õpetaja',
                           'õpil': 'õpilane'})

numbers = {'0': 'null',
           '1': 'üks',
           '2': 'kaks',
           '3': 'kolm',
           '4': 'neli',
           '5': 'viis',
           '6': 'kuus',
           '7': 'seitse',
           '8': 'kaheksa',
           '9': 'üheksa',
           2: 'tuhat',
           3: 'miljon',
           4: 'miljard',
           5: 'triljon',
           6: 'kvadriljon',
           7: 'kvintiljon',
           8: 'sekstiljon',
           9: 'septiljon',
           ',': 'koma',
           }

# vaikimisi väärtus puuduva võtme jaoks on tühisõne
numbers = defaultdict(lambda: '', numbers)

ordinal_numbers = {
    'üks': 'esimene',
    'kaks': 'teine',
    'kolm': 'kolmas',
    'neli': 'neljas',
    'viis': 'viies',
    'kuus': 'kuues',
    'seitse': 'seitsmes',
    'kaheksa': 'kaheksas',
    'üheksa': 'üheksas',
    'kümme': 'kümnes',
    'kümmend': 'kümnes',
    'teist': 'teistkümnes',
    'sada': 'sajas',
    'tuhat': 'tuhandes',
    'miljon': 'miljones',
    'miljard': 'miljardes',
    'triljon': 'triljones',
    'kvadriljon': 'kvadriljones',
    'kvintiljon': 'kvintiljones',
    'sekstiljon': 'sekstiljones',
    'septiljon': 'septiljones',
}

ordinal_numbers = defaultdict(lambda: '', ordinal_numbers)

vabamorf = Vabamorf()


# fn-i koodi põhi saadud siit: https://www.w3resource.com/python-exercises/class-exercises/python-class-exercise-2.php

def roman_to_int(s):
    rom_dict = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    rom_val = defaultdict(lambda: 0, rom_dict)
    int_val = 0
    for i in range(len(s)):
        if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
            int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
        else:
            int_val += rom_val[s[i]]
    return int_val


# funktsioon, mis teisendab kuni kolmenumbrilise osa arvust sõnadeks
def convert_a_block(number):
    # number: sõne kujul arv lemmatiseeritult (nt '110')

    if number == '':
        return ''
    # üheliikmelise arvu puhul võtame lihtsalt sõnastikust algvormi
    elif len(number) == 1:
        return numbers[number]
    # kaheliikmelise arvu korral kehtivad vastavad erijuhud
    elif len(number) == 2:
        if number[-1] == '0':
            if number[0] == '1':
                return 'kümme'
            elif number[0] == '0':
                return ''
            else:
                number_as_word = numbers[number[0]]
                return number_as_word + 'kümmend'
        elif number[0] == '1':
            number_as_word = numbers[number[1]]
            return number_as_word + 'teist'
        else:
            first_number_as_word = numbers[number[0]]
            second_number_as_word = numbers[number[1]]
            if number[0] == '0':
                return second_number_as_word
            else:
                return first_number_as_word + 'kümmend ' + second_number_as_word
    # kui arv koosneb kolmest elemendist (rohkemate elementidega ei peaks sellesse fn-i jõudma)
    else:
        first_number_as_word = numbers[number[0]]
        last_part = convert_a_block(number[1:])
        if number[0] == '0':
            return last_part
        else:
            return first_number_as_word + 'sada ' + last_part


# funktsioon, mis tükeldab arvu vajadusel osadeks ja seejärel teisendab osade kaupa
def convert_a_whole(number, is_sg_nom):
    # number: sõne kujul arv lemmatiseeritult (nt '110')
    # is_sg_nom: True, kui tegu on põhiarvsõna ainsuse nimetava käändega (sel juhul läheb
    # kohe nimetavale kujule, nt 'kaks miljonit ükssada' vs käänatav algvormis 'kaks miljon ükssada')

    # kui sisaldab punkti (nt kell 19.30), siis vaja eraldi teisendada osa enne punkti ja osa pärast punkti;
    # sama süsteem, kui sisaldab koolonit (nt 6:2 võit; ka sellisel kujul kellaajad, nt 19:30)
    index = None
    if '.' in number:
        index = number.index('.')
    elif ':' in number:
        index = number.index(':')
    elif '-' in number:
        index = number.index('-')

    if index:
        first_part = convert_a_whole(number[:index], is_sg_nom)
        last_part = convert_a_whole(number[index + 1:], is_sg_nom)
        return first_part + ' ' + last_part
    # koma puhul sama lähenemine, ainult et sõna 'koma' tuleb ka ise välja hääldada
    if ',' in number:
        index = number.index(',')
        first_part = convert_a_whole(number[:index], is_sg_nom)
        last_part = convert_a_whole(number[index + 1:], is_sg_nom)
        return first_part + ' koma ' + last_part

    # eemaldame üleliigsed punktid (juhtudel, kui arvu sees on mitu punkti järjest, nt 19...20)
    if number.startswith('.'):
        number = number.lstrip('.')
    # kontrollime, kas arv algab nulliga - kui jah, siis teisendus kujul 'null null ...',
    # vajalik nt kellaaegade puhul (00.30) või komakohtadega arvude puhul (3,04)
    match = re.match('^0+', number)
    if match:
        as_string = ''
        for elem in number:
            as_string += numbers[elem] + ' '
        return as_string
    # kui arv koosneb kuni kolmest numbrist
    if len(number) <= 3:
        return convert_a_block(number)
    # kui arv koosneb enam kui kolmest numbrist
    else:
        # loome kuni kolmeliikmelised plokid, kus samuti arv sõne kujul,
        # nt '110000' -> ['110', '000']
        blocks = []
        index = len(number)
        while index >= 3:
            block = number[index - 3:index]
            blocks.insert(0, block)
            index -= 3
        if index > 0:
            last_block = number[:index]
            blocks.insert(0, last_block)
    # vaatame järjest plokid läbi, teisendame ükshaaval
    # ja lisame vajalikud sõnad nagu 'miljon', 'tuhat' jms
    number_as_string = ''
    for i, block in enumerate(blocks):
        # vaatame, mitu elementi on plokkide järjendis antud plokist tagapool (plokk ise kaasa arvatud),
        # ja leiame vastava väärtuse numbrite sõnastikust (nt tuhat, miljon, miljard jne)
        no_of_blocks_right = len(blocks[i:])
        add_text = numbers[no_of_blocks_right]
        block_converted = convert_a_block(block)
        # kui plokk koosneb vaid nullidest, siis ei lisa lõppsõnele midagi
        if block != '000':
            # add_text võib olla ka tühisõne, sest viimase ploki puhul ei ole sõnastikus vastet
            if add_text != '':
                if is_sg_nom:
                    # üks miljon vs kaks/kolm/jne miljonit eristus
                    if no_of_blocks_right >= 3 and block_converted.strip() != 'üks':
                        add_text += 'it'
                number_as_string += block_converted + ' ' + add_text + ' '
            else:
                number_as_string += block_converted + ' '

    return number_as_string


# funktsioon, mis võtab sõne kujule teisendatud arvu ja normaliseerib selle

def normalize_string(number, number_as_string):
    # number: lemmatiseeritud sõne kujul arv, nt '100', ilma käändelõputa
    # number_as_string: sõnalisele algkujule viidud arv, nt 'sada'

    # eemaldame sõnade vahelt üleliigsed tühikud
    number_as_string = re.sub(r'\s{2,}', ' ', number_as_string)

    # eemaldame 'üks' sõne algusest, v.a juhul, kui arv ongi 1 või 11 (nt ükssada -> sada)
    # või siis, kui järgneb koma (nt üks koma viis), või kui arv on 1. (järgarv)
    match = re.match('^üks(?! koma|teist)', number_as_string)
    if len(number) > 1 and match and number != '1.':
        # asendame esimese (vasakpoolseima) ühe tühisõnega
        number_as_string = re.sub('üks', '', number_as_string, count=1)

    # eemaldame sõne ümbert üleliigsed tühikud
    number_as_string = number_as_string.strip()
    return number_as_string


# funktsioon, mis teisendab normaliseeritud sõne kujul arvu viimase osa järgarvuks

def make_ordinal(number_as_string, synthesizer):
    # number_as_string: sõnalisele kujule viidud arv, nt 'sada üks'
    # synthesizer: Vabamorfi instants

    parts_as_strings = number_as_string.split(' ')
    ordinal_parts_as_strings = []
    # kõik osad peale viimase jätame algvormi
    if len(parts_as_strings) > 1:
        for part in parts_as_strings[:-1]:
            ordinal_parts_as_strings.append(part)
    # viimase osa muudame järgarvuks
    final_part = parts_as_strings[-1]
    # kui viimase osa lõpp on 'teist', 'kümmend' või 'sada'
    special_suffix = None
    if final_part.endswith('teist'):
        special_suffix = 'teist'
    elif final_part.endswith('kümmend'):
        special_suffix = 'kümmend'
    elif final_part.endswith('sada') and final_part != 'sada':
        special_suffix = 'sada'
    if special_suffix:
        partition_tuple = final_part.partition(special_suffix)
        # kääname lõpueelset osa, nt 'üksteist' -> 'üheteistkümnes'
        synthesized = synthesizer.synthesize(partition_tuple[0], 'sg g')
        if len(synthesized) > 0:
            part_in_gen = synthesized[0]
            ordinal_parts_as_strings.append(part_in_gen + ordinal_numbers[special_suffix])
        else:
            ordinal_parts_as_strings = []
    # muul juhul asendame viimase osa lihtsalt vastega sõnastikust ordinal_numbers
    else:
        ordinal_parts_as_strings.append(ordinal_numbers[parts_as_strings[-1]])

    if len(ordinal_parts_as_strings) != 0:
        return ordinal_parts_as_strings
    # kui järgarvu kujule ei õnnestunud viia, siis jätame algvormi
    else:
        return parts_as_strings


def inflect(original_as_string, own_case, next_case, synthesizer, ordinal):
    # original_as_string: sõne, mis koosneb algvormis sõnadest (lemmadest)
    # own_case: sõna enda käändevorm
    # next_case: lauses järgmise sobiva sõnaliigiga sõna käändevorm
    # synthesizer: Vabamorfi instants
    # ordinal: True, kui tegu on järgarvuga

    # kui järgarv, siis esmalt viime selle viimase osa järgarvu kujule
    if ordinal:
        parts_as_strings = make_ordinal(original_as_string, synthesizer)
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


def inflect_a_quantifiable(prev_lemma, lemma, own_case, synthesizer, ordinal):
    # prev_lemma: märgile/ühikule eelnev lemma tekstis, nt 25% puhul on prev_lemma '25'
    # lemma: märgi/ühiku lemma, nt '%'
    # synthesizer: Vabamorfi instants

    if lemma in voc_symbol_dict:
        as_string = voc_symbol_dict[lemma]
    else:
        as_string = abbrev_dict[lemma]

    if as_string:
        # kui oma kääne on määratud (ja mitte ainsuse nimetav), siis kääname selle järgi
        if own_case not in ('', '?', 'sg n'):
            as_string = inflect(as_string, own_case, '', synthesizer, ordinal)
        # muul juhul kääname eelneva arvu järgi
        elif prev_lemma != 'üks' and prev_lemma != '1':
            as_string = inflect(as_string, 'sg p', '', synthesizer, ordinal)
        return as_string
    else:
        return lemma


def get_string(text, index, tag, synthesizer):
    # text: lausest tehtud Text-objekt
    # index: teisendatava sõne asukoht lauses
    # tag: sõnele määratud märgend
    # synthesizer: Vabamorfi instants

    ordinal = False
    ending_lemma = ''
    beginning_lemma = ''

    # võtame esimese lemma
    lemma = text.morph_analysis.lemma[index][0]

    # kontrollime, ega lemmatiseerimisel pole sõnesiseseid punkte kaduma läinud
    # (nt 2.3.2018 võib muutuda '232018'-ks)
    if 1 < lemma.count('.') < text.words[index].text.count('.'):
        lemma = text.words[index].text

    # kontrollime, et lemmatiseerimisel ei oleks häälduvat sümbolit sõna algusest kaduma läinud
    # (nt +4 võib muutuda 4-ks)
    if text.words[index].text[0] in voc_symbol_dict and lemma[0] not in voc_symbol_dict:
        lemma = text.words[index].text[0] + lemma

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
        as_arabic = roman_to_int(lemma)
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
            if re.match(r'(\d+\.?,?\s)+(ja|või)\s\d', text.text[text.words[index].start:]):
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

        # järgmisena vaatame, kas ees või järel on käänet määrav sõna (vaatame kuni kaks sõna edasi/tagasi,
        # sest nt 'Hind tõusis 5 € peale', 'Üle 2 km on juba läbitud')
        if next_case in ('', '?'):
            if index > 0:
                prev_lemma = text.words[index - 1].lemma[0]
                if prev_lemma in pre_gens:
                    own_case = 'sg g'
                    next_case = 'sg g'
                elif prev_lemma in pre_noms:
                    own_case = 'sg n'
                    next_case = 'sg n'
            if (index < len(text.words) - 1 and text.words[index + 1].lemma[0] in post_gens) \
                    or (index > 1 and text.words[index - 2].lemma[0] in pre_gens) \
                    or (index < len(text.words) - 2 and text.words[index + 2].lemma[0] in post_gens):
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
        as_string = convert_a_whole(lemma, is_sg_nom)
        # normaliseerime
        as_string = normalize_string(lemma, as_string)

    else:
        # kui lühend/sümbol lause või otsekõne alguses, siis kontrollime, kas lemma esisuurtähega.
        # kui jah, siis viime väiketähtkujule
        if index == 0 or (index > 0 and text.words[index - 1].text == '"') and lemma.istitle():
            lemma = lemma[0].swapcase() + lemma[1:]
        # leiame teisenduse sõnastikust
        if lemma in voc_symbol_dict:
            as_string = voc_symbol_dict[lemma]
        else:
            as_string = abbrev_dict[lemma]

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
                as_string = inflect(as_string, 'sg g', next_case, synthesizer, ordinal)
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
                        as_string = inflect(as_string, genitive, next_case, synthesizer, ordinal)
                    else:
                        as_string = inflect(as_string, own_case, next_case, synthesizer, ordinal)
                    inflected = True
                # järgmise sõna järgi kääname ainult siis, kui sõnalõpp ei ole kvantifitseeritav
                # või kui on tegu omadussõnalise fraasiga
                elif ending_lemma not in quantifiables or is_adj_phrase:
                    as_string = inflect(as_string, own_case, next_case, synthesizer, ordinal)
                    inflected = True

                # käändumatute vormide puhul jääb sõnalõpp algkujule
                if tag == 'K':
                    ending = ending_lemma
                # muul juhul tuleb sõnalõppu samuti käänata (kui sõna enda kääne määramata, siis
                # vastavalt eelnevale arvule või kui tegu omadussõnalise fraasiga, siis vastavalt next_case'ile)
                elif ending_lemma in quantifiables:
                    if is_adj_phrase:
                        ending = inflect_a_quantifiable(lemma, ending_lemma, next_case, synthesizer, ordinal)
                    else:
                        ending = inflect_a_quantifiable(lemma, ending_lemma, own_case, synthesizer, ordinal)
                else:
                    ending = inflect(ending_lemma, own_case, next_case, synthesizer, ordinal)

            # kui omadussõnaline ja põhiosa koosneb vaid ühest sõnast, siis kirjutame põhiosa ja lõpu kokku
            if tag == 'A' and (len(as_string.split(' ')) == 1 or ending == 'ne'):
                as_string += ending
            else:
                as_string += ' ' + ending

        if len(beginning_lemma) > 0:
            beginning = ''
            # kääname põhiosa vaid siis, kui veel pole käänatud
            if not inflected:
                as_string = inflect(as_string, own_case, next_case, synthesizer, ordinal)
            # käändumatute vormide puhul jääb algus algkujule
            if tag == 'K':
                beginning = beginning_lemma
            elif beginning_lemma in voc_symbol_dict:
                if beginning_lemma == '-':
                    # erandjuhtudel, nt aadressides nagu Aia 1a-23, jääb -23 eraldi lemmaks. miinuse
                    # eksliku hääldamise vältimiseks kontrollime, mis sellele vahetult eelneb
                    beginning_loc = text.words[index].start
                    if beginning_loc == 0 or (beginning_loc > 0 and text.text[beginning_loc - 1] in (' ', '(', '"')):
                        beginning = 'miinus'
                else:
                    beginning = voc_symbol_dict[beginning_lemma]
            else:
                beginning = beginning_lemma
            # liidame alguse õige vormi põhiosale
            as_string = beginning + ' ' + as_string

    elif (tag == 'M') and (own_case in ('', '?', 'sg n')):
        # kui tegu on kvantifitseeritava sümboliga/ühikuga, aga own_case määramata või ainsuse nimetav,
        # siis vaatame eelmist sõna (kui on), nt 1 dollar vs 11 dollarit
        if lemma in quantifiables:
            if index > 0:
                prev_postag = text.words[index - 1].partofspeech[0]
                prev_lemma = text.words[index - 1].lemma[0]
                # kui eelmine sõna on arvsõna, siis kääname vastavalt arvule
                if prev_postag in ('N', 'O'):
                    # erandjuhul, kui kuulub omadussõnafraasi, siis läheb omastavasse (nt 15 cm pikkune)
                    if is_adj_phrase:
                        own_case = 'sg g'
                    as_string = inflect_a_quantifiable(prev_lemma, lemma, own_case, synthesizer, ordinal)
        # kui ei ole kvantifitseeritav, siis oma käände puudumisel lühendit/sümbolit ei kääna
        else:
            return as_string
    else:
        as_string = inflect(as_string, own_case, next_case, synthesizer, ordinal)
    return as_string


def convert_sentence(sentence, synthesizer):
    # sentence: sõne kujul lause
    # synthesizer: Vabamorfi instants

    # teostame lausel morf. analüüsi
    text = Text(sentence).analyse('morphology')

    # loome märgendite sõnastiku, kus võtmeteks saavad
    # 'N' - põhiarvsõnad;
    # 'O' - järgarvsõnad;
    # 'M' - muud (ehk häälduvad sümbolid, lühendid, ühikud);
    # 'A' - omadussõnalised vormid (ehk nt ne-liitelised nagu 10-aastane),
    # 'K' - käändumatud vormid nagu aadressid ja klassid, kus liide ei ole lühend;
    # ja väärtusteks järjend sõnade indeksitest, mille kohta märgend käib

    tag_indices = defaultdict(lambda: [])
    num_postags = ('N', 'O')
    misc_postags = ('Z', 'Y', 'J', 'A')
    # vaatame järjest läbi igale sõnale antud märgendid
    for i, postag_list in enumerate(text.morph_analysis.partofspeech):
        added = False
        text_string = text.words[i].text
        text_lemma = text.words[i].lemma[0]
        last_index = len(text.words) - 1
        # võtame esimese sõnaliigimärgendi (nagu ka esimese lemma)
        postag = postag_list[0]
        # sõnastikku paneme indeksi ainult siis, kui vastab meie kriteeriumidele
        if postag in misc_postags:
            # lühendid lause või otsekõne alguses võivad saada esisuurtähega lemmad, viime väiketähtkujule
            if i == 0 or (i > 0 and text.words[i - 1].text == '"') and text_lemma.istitle():
                text_lemma = text_lemma[0].swapcase() + text_lemma[1:]
            if text_lemma in voc_symbol_dict or text_lemma in abbrev_dict:
                if text_lemma not in in_betweens:
                    tag_indices['M'].append(i)
                    added = True
                # sümbolid, mis saavad teisenduse vaid siis, kui asuvad kahe arvsõna vahel
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
                        added = True
            # ne-liitelised arvu sisaldavad sõnad asetame omadussõnaliste alla
            elif postag in ('Y', 'A') and re.match(r'^\d+-?\w*ne$', text_lemma):
                tag_indices['A'].append(i)
                added = True
            # aadresside, klasside jms käsitlemine, kus sõnaliigiks Y, nt Pärna 14a või 5b
            elif postag == 'Y' and re.search(r'\d+-?\w?$', text_lemma):
                tag_indices['K'].append(i)
                added = True

        elif postag in num_postags:
            if re.search(r'\d+', text_string):
                # muudame lause lõpus oleva 'O' märgendi 'N'-iks (lauselõpupunkt muudab alati eelneva arvu järgarvuks);
                # käändelõppudega arvud määratakse tihti asjatult järgarvudeks
                if (postag == 'O' and '.' not in text_string and not re.search(r'\d+-?nd', text_string)) \
                        or (postag == 'O' and i == last_index):
                    postag = 'N'
                tag_indices[postag].append(i)
                added = True

        # Rooma numbrite käsitlemine (sõnaliigiks saab automaatselt 'O' või käänatuna 'Y'
        # või käändumatu lõpuga 'H')
        if not added:
            # vaatame lemmat ehk selle tingimuslause alla mahuvad ka õigesti käänatud ja
            # käändelõppudega juhtumid, nt VI-le, IIIks
            if postag in ('O', 'Y') and re.match('^[IVXLCDM]+$', text_lemma):
                # erandjuhtum on 'C', mida ei tohi teisendada 'sajandaks', kui eelneb kraadimärk (Celsius)
                if text_lemma == 'C' and i > 0:
                    if text.words[i - 1].text != '°':
                        tag_indices['O'].append(i)
                else:
                    tag_indices['O'].append(i)
            # juhtumid nagu nt VIIa või Xb klass võivad saada kas 'Y' või 'H' märgendi;
            # lõppu lubame vaid ühe väiketähe, et vältida pärisnimede nagu
            # Mai või Ivi Rooma numbriteks arvamist
            elif postag in ('Y', 'H') and re.match('^[IVXLCDM]+[a-h]?$', text_lemma):
                tag_indices['O'].append(i)

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
                in_string_form = get_string(text, index, tag, synthesizer)
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
        return new_sentence
    else:
        return sentence
