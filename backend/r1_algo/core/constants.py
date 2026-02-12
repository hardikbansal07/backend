
# The Avakahada Chakra: Maps Nakshatra Padas to Sounds
AVAKAHADA_CHAKRA = {
    "Ashwini": ["Chu", "Che", "Cho", "La"],
    "Bharani": ["Li", "Lu", "Le", "Lo"],
    "Krittika": ["A", "I", "U", "E"],
    "Rohini": ["O", "Va", "Vi", "Vu"],
    "Mrigashirsha": ["Ve", "Vo", "Ka", "Ki"],
    "Ardra": ["Ku", "Gha", "Ng", "Jha"],
    "Punarvasu": ["Ke", "Ko", "Ha", "Hi"],
    "Pushya": ["Hu", "He", "Ho", "Da"],
    "Ashlesha": ["Di", "Du", "De", "Do"],
    "Magha": ["Ma", "Mi", "Mu", "Me"],
    "Purva Phalguni": ["Mo", "Ta", "Ti", "Tu"],
    "Uttara Phalguni": ["Te", "To", "Pa", "Pi"],
    "Hasta": ["Pu", "Sha", "Na", "Tha"],
    "Chitra": ["Pe", "Po", "Ra", "Ri"],
    "Swati": ["Ru", "Re", "Ro", "Ta"],
    "Vishakha": ["Ti", "Tu", "Te", "To"],
    "Anuradha": ["Na", "Ni", "Nu", "Ne"],
    "Jyeshtha": ["No", "Ya", "Yi", "Yu"],
    "Mula": ["Ye", "Yo", "Bha", "Bhi"],
    "Purva Ashadha": ["Bhu", "Dha", "Pha", "Dha"],
    "Uttara Ashadha": ["Bhe", "Bho", "Ja", "Ji"],
    "Shravana": ["Ju", "Je", "Jo", "Gha"],
    "Dhanishta": ["Ga", "Gi", "Gu", "Ge"],
    "Shatabhisha": ["Go", "Sa", "Si", "Su"],
    "Purva Bhadrapada": ["Se", "So", "Da", "Di"],
    "Uttara Bhadrapada": ["Du", "Tha", "Jha", "Na"],
    "Revati": ["De", "Do", "Cha", "Chi"]
}

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Mapping of Sign Index (0-11) or Name to Lord might be useful, but here we stick to simple lists or dicts.
# RULERS map Sign Name to Ruling Planet
RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter"
}

SIGN_ELEMENTS = {
    "Fire": ["Aries", "Leo", "Sagittarius"],
    "Earth": ["Taurus", "Virgo", "Capricorn"],
    "Air": ["Gemini", "Libra", "Aquarius"],
    "Water": ["Cancer", "Scorpio", "Pisces"]
}

SIGN_MODALITIES = {
    "Movable": ["Aries", "Cancer", "Libra", "Capricorn"], # Chara
    "Fixed": ["Taurus", "Leo", "Scorpio", "Aquarius"],    # Sthira
    "Dual": ["Gemini", "Virgo", "Sagittarius", "Pisces"]  # Dvisvabhava
}

SIGN_DIRECTIONS = {
    "Aries": "East", "Leo": "East", "Sagittarius": "East",
    "Taurus": "South", "Virgo": "South", "Capricorn": "South",
    "Gemini": "West", "Libra": "West", "Aquarius": "West",
    "Cancer": "North", "Scorpio": "North", "Pisces": "North"
}

ASPECTS = {
    "Saturn": [3, 7, 10],
    "Jupiter": [5, 7, 9],
    "Mars": [4, 7, 8],
    "Sun": [7], "Moon": [7], "Mercury": [7], "Venus": [7], "Rahu": [5, 7, 9], "Ketu": [5, 7, 9] 
}

PLANET_HEIGHT_SCORES = {
    "Saturn": 1, "Rahu": 1, "Mercury": 1, 
    "Jupiter": 0, "Sun": 0,                
    "Mars": -1, "Venus": -1, "Moon": -1,   
    "Ketu": -1                             
}

TATWA_COMPLEXION = {
    "Fire": "Reddish / Fair",
    "Water": "Pale / Wheatish",
    "Air": "Dark / Wheatish",      
    "Earth": "Dark / Earthy"       
}

# Alias for Engine compatibility
NAKSHATRA_SOUNDS = AVAKAHADA_CHAKRA
