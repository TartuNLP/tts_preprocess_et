# Preprocessing script for Estonian text-to-speech applications
Converts Estonian texts to a suitable format for speech synthesis. That includes converting numbers, symbols and
 abbreviations to words while considering the other elements in the sentence and declining words to maintain agreement.

The script follows the rules of Estonian orthography. Internationally used forms are only converted when they don't
 conflict with any Estonian use cases.
- Ranges use a dash (not a hyphen).
- Long numbers are grouped by spaces (not commas or dots)
- Dashes between numbers that are separated by spaces are considered to be minuses, otherwise they are ranges
- Decimal fractions use commas (not dots) 

### Requirement:
- Python 3
- EstNLTK (>= 1.6.0)

### Features


- [x] Converting Arabian numbers to words, including numbers that are grouped with spaces. Example: `10 000 → kümme
 tuhat`
- [x] Detecting ordinal numbers and converting them. Example: `1. → esimene`
- [x] Detecting the correct case from a suffix. Example: `1-le → ühele`
- [x] Numbers followed by a *-ne*/*-line* adjective. Example: `1-aastane → ühe aastane`
- [x] Detecting the correct case from upcoming words and their forms. Example: `1 sõbrale → ühele sõbrale; 1 sõbraga → ühe sõbraga`
- [x] Detecting the correct case from adpositions. Example: `üle 1 → üle ühe; 1 võrra → ühe võrra`
- [x] Detecting and converting Roman numerals. Example: `I → esimene`
- [x] Declining numbers in simple lists. Example: `1. ja 2. juunil → esimesel ja teisel juunil`
- [x] Converting and declining audible symbols. Example: `% → protsent`
- [x] Converting and declining common abbreviations. Example: `jne → ja nii edasi`
- [x] Converting simple mathematic equations. Example: `1 + 1 = 2 → üks pluss üks võrdub kaks`
- [ ] Converting inequations. Example: `1 > 2 → üks on suurem kui kaks`
- [x] Converting ranges. Example: `1–5 → üks kuni viis`
- [x] Converting areas and volumes. Example: `1 x 2 x 8 m → üks korda kaks korda kaheksa meetrit`
- [x] Converting decimal fractions. Example: `0,0051 → null koma null null viis üks`
- [x] Dates. Example: `01.01.2000 → Null üks null üks kaks tuhat`
- [x] Times. Example: `12.30 → kaksteist kolmkümmend`
- [x] Scores. Example: `11:15 → üksteist viisteist`
- [x] Numbers that contain more than one dot. Example: `1.25.16,2 → `<del>`kaksteist tuhat viissada kuusteist koma kaks`</del>`üks kakskümmend viis kuusteist koma kaks`
- [ ] Converting capitalized abbreviations. Example: `ATV → aa-tee-vee; MP3 → emm-pee-kolm` 
- [ ] Converting URLs. Example: `www.eesti.ee → vee-vee-vee punkt eesti punkt ee-ee`
- [ ] Converting terminative Roman numerals. Example: `I. → esiteks`
- [ ] Handling conversions with multiple possible outcomes (producing all options or somehow picking the best one). Currently we have tried to opt for the interpretation that can be used in as many situations as possible. Example: `10.05 → `<del>`kümnes mai, kümme läbi viis minutit,`</del>` kümme null viis`
    - [ ] Abbreviations that have multiple uses. Currently each abbreviation is limited to one interpretation. Example: `v.a → [välja arvatud, väga austatud]`
    - [ ] Words that can be declined in different ways. Currently the first option produced by the Vabamorf synthesizer in EstNLTK is used. Example: `15 inimese → [viietest inimese, viieteistkümne inimese]; 3. inimest → [kolmat inimest, kolmandat inimest]`
    - [ ] A dash between numbers that contain spaces. Currently we assume that it is a mathematical equation and not a range. Example: `5000 – 10 000 → [viis tuhat miinus kümme tuhat, viis tuhat kuni kümme tuhat]`
    - [ ] Roman numerals that may also be abbreviations. Currently we assume them to be numerals except for 'C'. Example: `C → [Celsius, sajas]; I → [üks, voolutugevus]`
    - [ ] Differentiating simple fractions from years, addresses, etc. Currently there is no support for simple fractions. Example: `2/5 → [kaks viis, kaks viiendikku]`
    - [ ] Numbers at the end of a sentence (followed by a dot) could be either cardinal or ordinal. Currently converted to cardinal numbers.
- [ ] Converting special cases of numbers, such as national ID numbers, phone numbers, etc.
- [x] Ranges that use three dots. Example: `1...5 → `<del>`üks viis`</del>` üks kuni viis`
- [ ] Numbers grouped by spaces followed by a *-ne*/*-line* adjective. Example: `20 300-eurone tšekk → `<del>`kahekümne kolmesaja eurone tšekk`</del>` kahekümne tuhande kolmesaja eurone tšekk`
- [x] Simple addresses. Example: `2-10 → kaks kümme; 5b → viis b`
- [ ] Addresses with an apartment number and a specifying letter. Example: `5a-1 → viis a üks`
- [ ] Converting letters in classes and addresses. Example: `Ib → esimene `<del>`b`</del>` bee; 1b → üks `<del>`b
`</del>` bee`
- [ ] Censored words should not be interpreted as abbreviations. Example: `p***e → `<del>`punkt***ehk`</del>
- [ ] Detecting abbreviated *-ne*/*-line* adjectives. Example: `5 km vahemaa → `<del>`viis kilomeetrit`</del>` viie kilomeetrine vahemaa`
- [ ] Numbers larger than 10^27
- [ ] Handling unmapped use cases: post-processing to make sure that all information that remains in the output is readable for speech synthesis and potentially creating a more robust mode where everything is always converted but disregarding the correct form.
