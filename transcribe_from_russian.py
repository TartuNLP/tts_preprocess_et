import rusyllab
import re

d = {
    'а': 'a',
    'б': 'b',
    'в': 'v',
    'г': 'g',
    'д': 'd',
    'ж': 'ž',
    'з': 'z',
    'к': 'k',
    'л': 'l',
    'м': 'm',
    'н': 'n',
    'о': 'o',
    'п': 'p',
    'р': 'r',
    'т': 't',
    'у': 'u',
    'ф': 'f',
    'ц': 'ts',
    'ч': 'tš',
    'ш': 'š',
    'щ': 'štš',
    'ъ': '',
    'ы': 'õ',
    'э': 'e',
    'ю': 'ju'
}

alphabet = ['а', 'б', 'в', 'г', 'д', 'ж', 'з', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'т', 'у', 'ф', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'э', 'ю', 'и', 'й', 'е', 'ё', 'с', 'х', 'ь', 'я']

vowels = ['а', 'э', 'ы', 'о', 'у', 'я', 'е', 'и', 'ё', 'ю']


def number_of_syllables(word):
    return len(rusyllab.split_word(word))


# "и" : üldjuhul "i"/sõna algul vokaali ees "j"
# "й" : üldjuhul "i"/sõna algul vokaali ees "j"
# "ий" : üldjuhul "ii"/kahe- ja enamasilbilise sõna lõpul "i"
def case_i(word, index):
    if len(word) > 1:
        if index == 0 and word[index + 1] in vowels:
            return 'j'
        elif index == len(word) - 1 and word[(len(word) - 2):] == 'ий' and number_of_syllables(word) >= 2:
            return ''
    return 'i'


# "e" : üldjuhul "e"/sõna algul, samuti vokaali, ь- ning ъ-märgi järel "je"
def case_e(word, index):
    if index == 0 or word[index - 1] in vowels or word[index - 1] == 'ъ':
        return 'je'
    return 'e'


# "ё" : üldjuhul "jo"/ж, ч, ш, щ järel "o"; Märkus. Täht е-ga märgitud ё transkribeeritakse nagu ё
def case_jo(word, index):
    if index > 0 and word[index - 1] in ['ж', 'ч', 'ш', 'щ', 'ь']:
        return 'o'
    return 'jo'


# "с" : üldjuhul "s"/vokaalide vahel ja sõna lõpul vokaali järel "ss"; Märkus. Liitsõnalise nime järelkomponendi algul oleva с-i võib asendada ühekordse s-iga (Новосибирск = Novosibirsk)
def case_s(word, index):
    if index > 0:
        if index == len(word) - 1 and word[index - 1] in vowels or index < len(word) - 1 and word[index - 1] in vowels and word[index + 1] in vowels:
            return 'ss'
    return 's'


# "х" : üldjuhul "h"/vokaalide vahel ja sõna lõpul vokaali järel "hh"; Märkus. Liitsõnalise nime järelkomponendi algul oleva х võib asendada ühekordse h-ga (Самоходов = Samohodov)
def case_h(word, index):
    if index > 0:
        if index == len(word) - 1 and word[index - 1] in vowels or index < len(word) - 1 and word[index - 1] in vowels and word[index + 1] in vowels:
            return 'hh'
    return 'h'


# "ь" : üldjuhul jääb märkimata/vokaali, välja arvatud e, ё, ю, я ees "j"
def case_snak(word, index):
    if index < len(word) - 1:
        if word[index + 1] in ['e', 'ё']:
            return 'j'
    return ''


# "я" : üldjuhul "ja"/Väljaspool dokumente ja teatmeteoseid võib eesnimede lõpul и järel я asendada a-ga (Евгения = Jevgenia, Лидия = Lidia)
def case_ja(word, index):
    return 'ja'


def transcribe_word(word):
    lower_word = word.lower()

    new_word = ''
    for index in range(len(lower_word)):
        if lower_word[index] in d.keys():
            new_word += d[lower_word[index]]
        elif lower_word[index] in ['и', 'й']:
            new_word += case_i(lower_word, index)
        elif lower_word[index] == 'е':
            new_word += case_e(lower_word, index)
        elif lower_word[index] == 'ё':
            new_word += case_jo(lower_word, index)
        elif lower_word[index] == 'с':
            new_word += case_s(lower_word, index)
        elif lower_word[index] == 'х':
            new_word += case_h(lower_word, index)
        elif lower_word[index] == 'ь':
            new_word += case_snak(lower_word, index)
        elif lower_word[index] == 'я':
            new_word += case_ja(lower_word, index)

    # Kas algas suure tähega
    if lower_word != word:
        return new_word.capitalize()
    else:
        return new_word


def transcribe_text(text):
    words = re.findall(r"\w+|[^\w\s]|[\s]", text, re.UNICODE)
    output = []
    for word in words:
        if word.isalpha() and False not in [i in alphabet for i in word.lower()]:
            word = transcribe_word(word)
        output.append(word)
    return ''.join(output)
