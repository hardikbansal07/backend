# Canonical Nakshatra name normalization utilities
# Exposed for API layer so outputs use standardized spellings.
# Canonical list (27):
# 1 Ashwini, 2 Bharani, 3 Krittika, 4 Rohini, 5 Mrigashira, 6 Ardra, 7 Punarvasu, 8 Pushya, 9 Ashlesha,
# 10 Magha, 11 Purva Phalguni, 12 Uttara Phalguni, 13 Hasta, 14 Chitra, 15 Swati, 16 Vishakha,
# 17 Anuradha, 18 Jyeshtha, 19 Mula, 20 Purva Ashadha, 21 Uttara Ashadha, 22 Shravana,
# 23 Dhanishtha, 24 Shatabhisha, 25 Purva Bhadrapada, 26 Uttara Bhadrapada, 27 Revati
# (Abhijit optional/intercalary; excluded from canonical 27)
from __future__ import annotations
import re

CANONICAL_NAKSHATRAS = [
    'Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha',
    'Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'
]

# Build variant map: (lowercased, alphanumeric stripped) -> canonical
_VARIANTS = {
    # 1
    'aswini':'Ashwini','ashvini':'Ashwini','ashwini':'Ashwini','aswathi':'Ashwini','aswati':'Ashwini',
    # 2
    'bharani':'Bharani','barani':'Bharani',
    # 3
    'karthigai':'Krittika','karthika':'Krittika','krittika':'Krittika','krithika':'Krittika','cartika':'Krittika',
    # 4
    'rohini':'Rohini',
    # 5
    'mrigashira':'Mrigashira','mrigshira':'Mrigashira','mrigasira':'Mrigashira','mrigasheersha':'Mrigashira','mrigasheesham':'Mrigashira','mrigasira':'Mrigashira','mrigashirsha':'Mrigashira',
    # 6
    'ardra':'Ardra','arudra':'Ardra','thiruvaathirai':'Ardra','thiruvathirai':'Ardra','tiruvadirai':'Ardra','thiruvadirai':'Ardra','thuruvathira':'Ardra',
    # 7
    'punarvasu':'Punarvasu','punarpoosam':'Punarvasu','punarphalguni':'Punarvasu',
    # 8
    'pushya':'Pushya','poosam':'Pushya','pooyam':'Pushya','pusya':'Pushya',
    # 9
    'ashlesha':'Ashlesha','aslesha':'Ashlesha','ayilyam':'Ashlesha','aayilyam':'Ashlesha','ayilya':'Ashlesha',
    # 10
    'magha':'Magha','makam':'Magha','makha':'Magha',
    # 11
    'purvaphalguni':'Purva Phalguni','poorvaphalguni':'Purva Phalguni','poorvam':'Purva Phalguni','pooram':'Purva Phalguni','puram':'Purva Phalguni',
    # 12
    'uttaraphalguni':'Uttara Phalguni','uthiram':'Uttara Phalguni','uttiram':'Uttara Phalguni','uttaram':'Uttara Phalguni',
    # 13
    'hasta':'Hasta','hastham':'Hasta',
    # 14
    'chitra':'Chitra','chithra':'Chitra','chithirai':'Chitra','chithirai':'Chitra','chitraa':'Chitra',
    # 15
    'swati':'Swati','swathi':'Swati','swaati':'Swati','swaathi':'Swati',
    # 16
    'vishakha':'Vishakha','visakha':'Vishakha','visaakam':'Vishakha','visakam':'Vishakha',
    # 17
    'anuradha':'Anuradha','anusham':'Anuradha','anuradha':'Anuradha',
    # 18
    'jyeshtha':'Jyeshtha','jyestha':'Jyeshtha','jyesta':'Jyeshtha','kaettai':'Jyeshtha','kettai':'Jyeshtha','ketta':'Jyeshtha','kettai':'Jyeshtha','jettha':'Jyeshtha','kaettai':'Jyeshtha',
    # 19
    'mula':'Mula','moolam':'Mula','mool':'Mula',
    # 20
    'purvaashadha':'Purva Ashadha','purvashadha':'Purva Ashadha','pooraadam':'Purva Ashadha','pooraadham':'Purva Ashadha','pooraadam':'Purva Ashadha','purvaashada':'Purva Ashadha',
    # 21
    'uttaraashadha':'Uttara Ashadha','uttarashadha':'Uttara Ashadha','uthiraadam':'Uttara Ashadha','uthiradam':'Uttara Ashadha','uthraadam':'Uttara Ashadha','uttiraadam':'Uttara Ashadha',
    # 22
    'shravana':'Shravana','sravana':'Shravana','thiruvonam':'Shravana','tiruvonam':'Shravana','thiruvon':'Shravana','thiruvonam':'Shravana',
    # 23
    'dhanishtha':'Dhanishtha','dhanishta':'Dhanishtha','avittam':'Dhanishtha','avittam':'Dhanishtha','avitt':'Dhanishtha',
    # 24
    'shatabhisha':'Shatabhisha','shatabhishta':'Shatabhisha','satabhisha':'Shatabhisha','satabhishak':'Shatabhisha','satabhisha':'Shatabhisha','sadhayam':'Shatabhisha',
    # 25
    'purvabhadrapada':'Purva Bhadrapada','poorattathi':'Purva Bhadrapada','poorvabhadra':'Purva Bhadrapada','purvabhadra':'Purva Bhadrapada','poorvabhadrapada':'Purva Bhadrapada',
    # 26
    'uttarabhadrapada':'Uttara Bhadrapada','uthirattathi':'Uttara Bhadrapada','uttarabhadra':'Uttara Bhadrapada','uttirattati':'Uttara Bhadrapada','uttirattathi':'Uttara Bhadrapada',
    # 27
    'revati':'Revati','revathi':'Revati','revathi':'Revati',
    # 28 (optional)
    'abhijit':'Abhijit','abhijith':'Abhijit'
}

_DEFALT_MAP = {re.sub(r'[^a-z]','', k.lower()): v for k,v in _VARIANTS.items()}

def normalize_nakshatra(name: str | None) -> str | None:
    if not name:
        return name
    key = re.sub(r'[^a-z]','', name.lower())
    return _DEFALT_MAP.get(key, name)

# Optionally produce the canonical list from any internal list

def to_canonical_list(raw_list):
    out = []
    for n in raw_list:
        cn = normalize_nakshatra(n)
        # Skip Abhijit if list should be only 27
        if cn == 'Abhijit':
            continue
        out.append(cn)
    # Preserve order but ensure uniqueness
    seen = set()
    unique = []
    for n in out:
        if n not in seen:
            unique.append(n); seen.add(n)
    return unique
