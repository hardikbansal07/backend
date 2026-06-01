# astrology_metadata.py
# AstroCare AI — Astrological Expert System Metadata Engine
# Optimized for high-speed, highly accurate LLM (Gemini) parsing

from typing import Optional

# ZODIAC LORDS Mapping
ZODIAC_LORDS = {
    1: "Mars",      # Aries
    2: "Venus",     # Taurus
    3: "Mercury",   # Gemini
    4: "Moon",      # Cancer
    5: "Sun",       # Leo
    6: "Mercury",   # Virgo
    7: "Venus",     # Libra
    8: "Mars",      # Scorpio
    9: "Jupiter",   # Sagittarius
    10: "Saturn",   # Capricorn
    11: "Saturn",   # Aquarius
    12: "Jupiter"    # Pisces
}

# ─────────────────────────────────────────────────────────────────────────────
# HOUSE CLASSIFICATIONS (Complete Structural Vedic Categories from Chart)
# ─────────────────────────────────────────────────────────────────────────────
HOUSE_CLASSIFICATIONS = {
    "Kendra": {
        "houses": [1, 4, 7, 10],
        "meaning": "Pillars of Life. Most powerful & important houses. Planets placed here exert a highly active, strong, and positive influence."
    },
    "Kona": {
        "houses": [1, 5, 9],
        "meaning": "Trikona (Fortune). Houses of growth, prosperity, wisdom, creativity, and spiritual merit. Extremely auspicious."
    },
    "Upachaya": {
        "houses": [3, 6, 10, 11],
        "meaning": "Houses of Growth. Strength and results multiply continuously with age. Challenges here eventually turn into major successes through self-effort."
    },
    "Dusthana": {
        "houses": [6, 8, 12],
        "meaning": "Malefic Houses. Represent lessons, debt, obstacles, and losses. While bringing challenges, they provide powerful opportunities for inner transformation."
    },
    "Panaphara": {
        "houses": [2, 5, 8, 11],
        "meaning": "Succedent Houses. Focus on resource accumulation, wealth retention, progeny, hidden reserves, and deep desires. They sustain and feed the Kendra houses."
    },
    "Apoklima": {
        "houses": [3, 6, 9, 12],
        "meaning": "Cadent Houses. Govern communication, changes, travel, intellect, external dependencies, and eventual letting go/detachment."
    },
    "Caturasra": {
        "houses": [4, 8],
        "meaning": "Defensive / Security Houses. Focus on emotional boundaries, homeland/home security (4th), and protection of vital life energies/deep hidden reserves (8th)."
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# HOUSE KNOWLEDGE (Optimized for rapid LLM processing & astrological grounding)
# ─────────────────────────────────────────────────────────────────────────────
HOUSE_KNOWLEDGE = {
    1: {
        "name": "1st House",
        "sanskrit_name": "Ascendant (Lagna)",
        "ruler": "Mars",
        "natural_zodiac": "Aries",
        "classifications": ["Kendra", "Kona"],
        "concept": "House of Self & Beginnings",
        "description": "Represents the absolute physical self, head, face, general health, attitude, and beginnings of life. Dictates 50% of the native's overall personality, body structure, and temperament, heavily driven by the Lagna sign and any occupying planets.",
        "represents": [
            "Self", "Nature", "Personality", "Body Structure", "Head", "Face", 
            "Mind", "Pituitary gland", "Health", "Fitness", "Attitude", 
            "Behaviour", "Self-Branding"
        ],
        "core_themes": {
            "Self & Ego (Individuality)": "Your core identity, basic temperament, personality traits, and natural posture toward life.",
            "Physical Appearance & Body Structure": "Physical representation of the self, height, face, skull shape, head, and outer presentation.",
            "Vitality, Health & Fitness": "Core physical health, energy level, recovery index, pituitary gland function, and overall fitness.",
            "Self-Branding & Attitude": "How you project yourself to the world, self-branding, outer attitude, and behavioral signature.",
            "Ancestry & Beginnings": "The absolute entry point of your soul onto Earth and the initial environment at birth."
        }
    },
    2: {
        "name": "2nd House",
        "sanskrit_name": "Money House (Dhan bhav)",
        "ruler": "Venus",
        "natural_zodiac": "Taurus",
        "classifications": ["Panaphara"],
        "concept": "House of Wealth, Speech & Assets",
        "description": "Governs liquid money, bank balance, family, assets, jewels, food habits, right eye, voice tone, mouth, lips, nose, family property/business, and deep personal insecurities. It represents the foundational resources available to sustain an individual.",
        "represents": [
            "Money", "Bank balance", "Family", "Right Eye", "Nose", "Voice tone", 
            "Food", "Banking", "Mouth", "Family Property/Business", "Lips", 
            "Assets", "Jewellery/Gemstone", "Insecurity"
        ],
        "core_themes": {
            "Speech / Voice": "Tone, speed, vocabulary, and the weight/truthfulness of words.",
            "Family Lineage (Kutumb)": "The environment and ancestry you are born into.",
            "Wealth Accumulation": "The capacity to save money and build tangible assets.",
            "Food & Diet": "Eating preferences (Sattvic, Rajasic, or Tamasic).",
            "Face Value": "Physical representation of the face, neck, and throat."
        }
    },
    3: {
        "name": "3rd House",
        "sanskrit_name": "Effort House",
        "ruler": "Mercury",
        "natural_zodiac": "Gemini",
        "classifications": ["Upachaya", "Apoklima"],
        "concept": "House of Efforts, Courage & Communication",
        "description": "An Upachaya house representing courage, self-effort, younger siblings, internet/data, communication, media, books, writing, planning, hobbies, throat, arms, hands, short travels, and marketing. Its strength grows continuously with age.",
        "represents": [
            "Attraction", "Change of place", "Online", "Short Travel", "Communication", 
            "Media", "Internet and Data", "Documents", "Effort", "Marketing", "Book", 
            "Writing", "Ear", "Throat", "Arms", "Hands", "Younger Brother", "Courage", 
            "Bravery", "Strength", "Networking", "Planning", "Hobbies", "Property Sale"
        ],
        "core_themes": {
            "Neighbors & Immediate Surroundings": "Who lives next door and the condition of your home's entrance/gate.",
            "Subconscious Brain & Processing (CPU)": "How quickly you process information, your analytical skills, and the random thoughts that occupy your mind.",
            "Communication & Throat": "Vocal cords, singing, writing, and thyroid gland health.",
            "Courage (Parakram)": "How brave you are and how you respond to challenges.",
            "Hobbies & Interests": "What you like doing in your free time (e.g., sports, reading, gaming, arts).",
            "Short Travels & Driving": "Daily commuting, quick trips, and your driving style.",
            "Younger Siblings": "The relationship with and characteristics of younger brothers or sisters."
        }
    },
    4: {
        "name": "4th House",
        "sanskrit_name": "Comfort House (Sukh bhav)",
        "ruler": "Moon",
        "natural_zodiac": "Cancer",
        "classifications": ["Kendra", "Caturasra"],
        "concept": "House of Comforts, Mother & Homeland",
        "description": "Rules homeland, home environment, mother, land, houses, physical comforts, vehicles, luxury, school, heart, lungs, chest, hotels, architecture, and hospitality.",
        "represents": [
            "House", "Land", "Property", "Homeland", "Mother", "Comforts", "Luxury", 
            "Vehicles", "Chest", "Lungs", "Heart", "Hotels", "Architect", 
            "Hospitality", "Restaurant", "School"
        ],
        "core_themes": {
            "Home & Real Estate": "The physical home environment, property, land, and household items.",
            "Emotional Body & Core Values": "Represents true inner feelings, what brings you peace, and how you act when nobody is watching.",
            "Mother & Unconditional Service": "The relationship with the mother and the concept of selfless, loving service.",
            "Public Interaction": "How you deal with the masses and common people.",
            "Childhood Memories": "Early life experiences, traumas, and foundational psychological triggers.",
            "Inner Realization": "The depth of self-realization, inner satisfaction, and spiritual grounding."
        }
    },
    5: {
        "name": "5th House",
        "sanskrit_name": "House of Children (Santan Bhav)",
        "ruler": "Sun",
        "natural_zodiac": "Leo",
        "classifications": ["Kona", "Panaphara"],
        "concept": "House of Intelligence, Children & Romance",
        "description": "Governs children, love affairs, romance, wisdom, study/education, solution-oriented intelligence, creative execution, art, entertainment, stomach/digestion, recovery, and product development.",
        "represents": [
            "Study", "Wisdom", "Learning", "Children", "School", "Love", "Nature/Environment", 
            "Affairs", "Creativity", "Solutions", "Execution", "Entertainment", 
            "Enjoyment/Celebration", "Digest", "spinal cord", "Stomach", "Recovery", 
            "Romance", "Product Development", "Artistic Talent"
        ],
        "core_themes": {
            "Vision & Depth": "Future vision and analytical depth.",
            "Education & Schooling": "School life experiences and suited degrees.",
            "Mantra Siddhi & Spirituality": "Inclination toward specific deities/mantras.",
            "Punya Karma (Past Life Credit)": "Consolidated good deeds from previous lives.",
            "Love Life & Romance": "Attraction, romantic affairs, and sexual compatibility.",
            "Chair & Position": "Gaining authority and high societal status.",
            "Grandfather (Paternal) & Mother's Family": "Traits of the grandfather and the maternal lineage's wealth/speech.",
            "Children (Progeny)": "Birth and relationship with children."
        }
    },
    6: {
        "name": "6th House",
        "sanskrit_name": "House of Diseases and Enemy (Rog and Satru Bhav)",
        "ruler": "Mercury",
        "natural_zodiac": "Virgo",
        "classifications": ["Upachaya", "Dusthana", "Apoklima"],
        "concept": "House of Obstacles, Jobs & Competitions",
        "description": "An Upachaya and Dusthana house representing active competition, service/jobs, diseases, debt/loans, litigation, legal/medical professions, maternal uncles, servants, kidney, and standard human vices (anger, greed, jealousy).",
        "represents": [
            "Diseases", "Enemy", "Competition", "Service", "Conflicts", "Loan/Debt", 
            "Lawyer", "Doctor", "Servant", "Siblings", "Medical", "Litigation", 
            "Maternal Uncle", "Father's Profession", "Kidney", "Yoga", "Greed", 
            "Anger", "Lust", "Jealousy"
        ],
        "core_themes": {
            "Rules & Regulations": "SOPs, bureaucracy, and making/following rules.",
            "Workplace & Corporate Life": "Experience as an employee and handling subordinates.",
            "Disease (Roga)": "Physical ailments (especially kidney/urinary/lower abdomen) and dietary habits.",
            "Debt (Rina) & Litigation": "Loans, court cases, and financial obligations.",
            "Enemies (Shatru)": "People who cause trouble, and how you handle conflicts.",
            "The Six 'Anarthas'": "Lust, Anger, Greed, Illusion, Pride, and Envy.",
            "Maternal Lineage": "Maternal uncle (Mama) and paternal aunt (Bua).",
            "Competitive Exams": "Capacity to handle academic pressure and fight for positions."
        }
    },
    7: {
        "name": "7th House",
        "sanskrit_name": "House of Spouse and Marriage (Vivah bhav)",
        "ruler": "Venus",
        "natural_zodiac": "Libra",
        "classifications": ["Kendra"],
        "concept": "House of Spouse, Marriage & Partnerships",
        "description": "Governs marriage, spouse, opposite gender, business partnerships, retail, self-employment, trading, customer interactions, reproductive/sex organs, opposition, and deep meditation.",
        "represents": [
            "Marriage", "Spouse", "Opposite gender", "Daily Interaction", "Business", 
            "Partner", "Trading", "Self-Employment", "Reproductive organs", "Kidney", 
            "Urinary bladder", "Sex organs", "Customers", "Retail", "Opposition", 
            "Meditation"
        ],
        "core_themes": {
            "Marriage & Spouse": "The primary house for determining whether marriage will happen, the nature of your spouse, and marital compatibility.",
            "Business Partnerships": "Determines if you should enter into a business partnership, how your partners will behave, and whether you will face fraud or growth.",
            "Public Perception": "How the outside world views you and your general image in society.",
            "Private Parts (Genitals)": "Relates to physical intimacy and the health of reproductive organs.",
            "Mother's Inner Core": "Represents your mother's moral values and emotional happiness (as it is 4th from the 4th house).",
            "Father's Income & Desires": "Reflects your father's wealth and desires (11th from the 9th house). Note: If a father earns through corrupt means, it directly impacts the child's 7th house, causing marriage problems.",
            "The 'Killer' of Individuality": "The 7th house requires compromise, balance, and stepping down from your ego. It demands that you lose your pure 'individuality' to go along with someone else."
        }
    },
    8: {
        "name": "8th House",
        "sanskrit_name": "House of Pain and Obstacles (Dukh Bhav)",
        "ruler": "Mars",
        "natural_zodiac": "Scorpio",
        "classifications": ["Dusthana", "Panaphara", "Caturasra"],
        "concept": "House of Transformation, Secrets & Research",
        "description": "Rules pain, severe obstacles, accidents, deep research, occult sciences, astrology, technology, manufacture, sudden events (unearned money, sudden losses), secrets, mysteries, lifespan, and large intestine.",
        "represents": [
            "Research", "Samadhi", "Occult", "Problem", "Depression", "Pain", "Injury", 
            "Surgery", "Hurdle", "Obstacles", "Transformation", "Humiliation", 
            "Observation", "Mystery", "Hide", "Secret", "Mode of Death", "Life span", 
            "Deep science", "Large Intestine", "Accidents", "Sudden Events", 
            "Unearned Money", "Astrology", "Technology", "Manufacture", "Bribe/Dowry"
        ],
        "core_themes": {
            "The Occult & Hidden Knowledge": "Astrology, Numerology, Vastu, Tantra, deep healing, and exploring the dark/unseen world.",
            "In-Laws (Sasural)": "The family of your spouse, their wealth, and your relationship with them.",
            "Hidden Secrets & Traumas": "Things you will absolutely never share with anyone else. Can include hidden affairs, childhood abuse, deep regrets, and unerasable stains (badnami).",
            "Death & Prolonged Illness": "The nature of your physical passing, severe/chronic diseases, and near-death experiences.",
            "Sudden Wealth": "Unearned money, inheritance, insurance payouts, lottery, or buried treasure (hidden resources).",
            "Conditions in the Womb": "Represents the mother's mental state, fantasies, and experiences while the native was in her womb.",
            "Physical Body": "Represents the anal area and the excretory system.",
            "Decay & Rock Bottom": "The house of breakdown. It shows how relationships decay and what happens when you hit rock bottom, forcing a massive transformation."
        }
    },
    9: {
        "name": "9th House",
        "sanskrit_name": "House of Father, Luck and Wisdom (Gyan Bhav)",
        "ruler": "Jupiter",
        "natural_zodiac": "Sagittarius",
        "classifications": ["Kona", "Apoklima"],
        "concept": "House of Dharma, Higher Learning & Luck",
        "description": "Governs father, mentors/gurus, luck, spirituality, religion, long travels, higher education, colleges, philosophy, publishing, thighs, and professional consultancy.",
        "represents": [
            "Spirituality", "Luck", "Father", "Religion", "Religious place", 
            "Teachers/Mentors", "Higher Learning", "Long Travel", "Culture", 
            "Philosophy", "Consultancy/counselling", "Hip joints", "Thighs", 
            "Idealism", "Publication", "Colleges"
        ],
        "core_themes": {
            "Bhagya (Fortune)": "The level of luck and divine support a person receives in this lifetime.",
            "Blessings of Gurus, Deities & Universe": "The spiritual protection and guidance you receive from higher powers, specific deities, and your spiritual masters.",
            "Father, Gurus & Acharyas": "Represents the nature, teachings, and influence of your father, your spiritual guides, and even your bosses.",
            "Long-Term Goals & High Vision": "How big your goals are, your capacity to dream long-term, and how high you can go in life.",
            "Long-Distance Journeys": "Represents foreign travel, long trips, and pilgrimages.",
            "Discomfort Zone & Challenging Peace of Mind": "The 9th house constantly pushes you out of your comfort zone to achieve higher goals or spiritual realization, which challenges your everyday peace of mind.",
            "Moral Guidelines & Principles": "The rulebook of your life (e.g., waking up early, eating Sattvic food, respecting elders, attending temple).",
            "Higher Education": "University degrees, PhDs, and deep, philosophical studies.",
            "Maternal Issues & Child's Education": "Acts as the 6th from the 4th (showing mother's debts/diseases) and the 5th from the 5th (showing the educational path of your children)."
        }
    },
    10: {
        "name": "10th House",
        "sanskrit_name": "House of Career and Profession (Karma Bhav)",
        "ruler": "Saturn",
        "natural_zodiac": "Capricorn",
        "classifications": ["Kendra", "Upachaya"],
        "concept": "House of Career, Profession & Social Status",
        "description": "An Upachaya and Kendra house representing professional life, career, karma, public status, authority, respect, knee joints, government interactions, and administrative power.",
        "represents": [
            "Career", "Karma", "Profession", "Public", "Knee Joint", "Status", 
            "Respect", "Authority", "Government", "Administration", "Fame"
        ],
        "core_themes": {
            "Assigned Karma": "The specific duties or life path assigned to the soul in this lifetime.",
            "Capacity for Sacrifice & Endurance": "How much pressure, isolation, and hard work you can tolerate to achieve your goals.",
            "Career & Job": "Your profession, workplace environment, and the nature of your daily work.",
            "Public Fame & Recognition": "The reputation and fame you achieve specifically because of your work and achievements (not just personal popularity).",
            "Father's Financial Condition": "The wealth, financial stability, and family background of your father.",
            "Mother-in-Law": "Represents the mother-in-law (as it is the 4th house from the 7th house).",
            "Nishkam Karma": "The ultimate lesson of the 10th house is learning to perform your duties without ego or attachment to the results, acting as an instrument of a higher power."
        }
    },
    11: {
        "name": "11th House",
        "sanskrit_name": "House of Desire and Income (Iccha Bhav)",
        "ruler": "Saturn",
        "natural_zodiac": "Aquarius",
        "classifications": ["Upachaya", "Panaphara"],
        "concept": "House of Desire, Gains & Friend Circles",
        "description": "An Upachaya house representing cash flow, daily income, profits, fulfillment of desires, friend circles, elder siblings, societal work, ambitions, and ankle joints. Multiplies gains continuously.",
        "represents": [
            "Fulfilment of Desire", "Multiplication", "Friend circle", "Ambition", 
            "Gains", "Daily Income", "Profit", "Lower leg", "Ankle", "Elder Brother", 
            "Society", "NGOs", "Social Works"
        ],
        "core_themes": {
            "Fulfillment of Desires": "Your deepest wishes, ambitions, and the things you crave to achieve.",
            "Obsessive Nature & Rule-Breaking": "Shows the specific area of life where you possess an obsessive madness and where you are willing to break societal rules to get what you want.",
            "Destroyer of Peace": "Because it is 8th from the 4th house (house of peace/home), the pursuit of 11th house desires often destroys your inner peace or domestic harmony.",
            "Older Siblings": "The relationship, traits, and influence of your immediate older brother or sister.",
            "Extended Family Karma": "Represents your paternal uncle (Chacha), the grandfather's business/married life, and the mother's hidden affairs or unexplored desires (things the mother wanted but never got).",
            "Father's Subconscious": "Reflects the unfulfilled desires of the father that he projects onto the native to achieve on his behalf."
        }
    },
    12: {
        "name": "12th House",
        "sanskrit_name": "House of Detachment and Loss (Moksha Bhav)",
        "ruler": "Jupiter",
        "natural_zodiac": "Pisces",
        "classifications": ["Dusthana", "Apoklima"],
        "concept": "House of Detachment, Expenses & Isolation",
        "description": "Rules losses, expenses, failures, hospitalizations, courts/prisons, isolation, bedroom pleasures, sleep, foreign travels, sleep quality, feet, and final spiritual liberation (Moksha).",
        "represents": [
            "Bedroom", "Moksha", "Failure", "Disappointment", "Loss", "Expenses", 
            "Hospital", "Court", "Prison", "Isolations", "Sex", "Pleasure", 
            "Luxury Items", "Investment/Investor", "Foreign travel", "Sleep", 
            "Detachment", "Distraction", "Divorce", "Feet", "Separation", 
            "Liberation", "Donation"
        ],
        "core_themes": {
            "Sleep & Dreams": "How well you sleep, the nature of your dreams, and what happens in your subconscious state. It also represents the physical bedroom.",
            "Isolation & Confinement": "Places away from normal society, such as ashrams, monasteries, hospitals, jails, and foreign lands.",
            "Losses & Expenses": "Where your money goes, what you are forced to give up, and your capacity to donate or let go of material attachments.",
            "Liberation (Moksha) & Spirituality": "Deep meditation, spiritual liberation, and surrendering to a higher power.",
            "Physical Intimacy & Bedroom Life": "The private life between partners (bed pleasures) and domestic harmony (or domestic violence if afflicted).",
            "Family Connections": "Represents the peace of mind of your father (4th from the 9th), the fortune of your mother (9th from the 4th), and your maternal grandfather (Nana).",
            "Independent Professions": "Working in isolation, away from corporate structures, or working independently (freelancing, healing, foreign trade)."
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# UNIVERSAL ASTROLOGICAL MATRIX ENGINE
# ─────────────────────────────────────────────────────────────────────────────

ZODIAC_SIGN_TO_ID = {
    "Aries": 1,
    "Taurus": 2,
    "Gemini": 3,
    "Cancer": 4,
    "Leo": 5,
    "Virgo": 6,
    "Libra": 7,
    "Scorpio": 8,
    "Sagittarius": 9,
    "Capricorn": 10,
    "Aquarius": 11,
    "Pisces": 12
}

def resolve_lagna_sign_id(asc_sign: str) -> int:
    """Normalizes and maps a textual zodiac sign to its corresponding Vedic ID (1 to 12)"""
    if not asc_sign:
        return 1
    normalized = asc_sign.strip().capitalize()
    return ZODIAC_SIGN_TO_ID.get(normalized, 1)

def get_house_lord_circuit(start_house: int, lagna_sign_id: int, lord_placements: dict) -> list:
    """
    Computes the dynamic House Lord Circuit starting from 'start_house' based on D1 chart.
    Follows: current_house -> its zodiac sign -> the lord of that sign -> where it is placed.
    Stops when it hits a house that has already been visited (loop termination).
    """
    circuit = []
    visited = set()
    current_house = start_house
    
    # Standard Vedic sign names in order (1-indexed)
    sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    while current_house not in visited:
        visited.add(current_house)
        
        # 1. Sign of this house:
        sign_id = (lagna_sign_id + current_house - 2) % 12 + 1
        sign_name = sign_names[sign_id - 1]
        
        # 2. Lord of this sign:
        lord = ZODIAC_LORDS.get(sign_id)
        
        # 3. Where is this lord placed?
        placed_house = lord_placements.get(lord)
        if placed_house is None:
            # Fallback if placement data is missing
            placed_house = current_house
            
        # 4. Calculate step distance inclusive anticlockwise from current_house to placed_house:
        steps_inclusive = (placed_house - current_house) % 12 + 1
        
        step_entry = {
            "house": current_house,
            "sign_id": sign_id,
            "sign_name": sign_name,
            "lord": lord,
            "placed_house": placed_house,
            "steps_inclusive": steps_inclusive,
            "is_bhavat_bhavam": steps_inclusive == current_house
        }
        circuit.append(step_entry)
        
        # Move to the placed house of the lord
        current_house = placed_house
        
    return circuit

class AstrologicalMatrixEngine:
    """
    The Universal Astrological Matrix Engine.
    Lagna Shifter: Shifts the focus of the chart to any given main_house (acting as relative Lagna)
    and resolves relative house meanings to physical D1 chart locations.
    """
    
    @staticmethod
    def get_physical_house(main_house: int, relative_house: int) -> int:
        """Calculates the physical D1 house for a given relative house R from a main_house"""
        return (main_house + relative_house - 2) % 12 + 1

    @classmethod
    def resolve_shifted_matrix(cls, main_house: int, lagna_sign_id: int) -> dict:
        """
        Shifts the Lagna to 'main_house' and resolves relative house properties to physical D1 houses.
        Returns a dictionary mapping relative house numbers (1 to 12) to their physical house information and static metadata.
        """
        matrix = {}
        sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        for r in range(1, 13):
            h = cls.get_physical_house(main_house, r)
            sign_id = (lagna_sign_id + h - 2) % 12 + 1
            sign_name = sign_names[sign_id - 1]
            
            # Retrieve static house knowledge for relative house R (which acts as the semantic theme)
            static_knowledge = HOUSE_KNOWLEDGE.get(r, {})
            
            matrix[r] = {
                "relative_house_number": r,
                "physical_house_number": h,
                "zodiac_sign_id": sign_id,
                "zodiac_sign_name": sign_name,
                "concept": static_knowledge.get("concept", ""),
                "description": static_knowledge.get("description", ""),
                "represents": static_knowledge.get("represents", []),
                "core_themes": static_knowledge.get("core_themes", {}),
                "classifications": static_knowledge.get("classifications", [])
            }
            
        return matrix

# ─────────────────────────────────────────────────────────────────────────────
# EXHAUSTIVE REPRESENTATION KEYWORD RESOLVER (PREVENTS LLM HALLUCINATIONS)
# ─────────────────────────────────────────────────────────────────────────────

REPRESENTATION_KEYWORD_MAP = {
    # 1st House (Lagna / Self)
    "self": 1, "me": 1, "myself": 1, "personality": 1, "nature": 1, "character": 1, 
    "body structure": 1, "head": 1, "face": 1, "pituitary gland": 1, "health": 1, 
    "fitness": 1, "attitude": 1, "behaviour": 1, "self-branding": 1, "beginnings": 1,
    "mera": 1, "meri": 1, "mujhe": 1, "swasthya": 1, "roop": 1,
    
    # 2nd House (Dhan / Wealth / Family / Speech)
    "wealth": 2, "bank balance": 2, "saving": 2, "savings": 2, "speech": 2, "voice": 2, 
    "family lineage": 2, "kutumb": 2, "assets": 2, "jewels": 2, "gemstone": 2, "mouth": 2, 
    "lips": 2, "right eye": 2, "nose": 2, "food": 2, "diet": 2, "liquids": 2,
    "paisa": 2, "dhan": 2, "vanee": 2, "parivar": 2, "khana": 2,
    
    # 3rd House (Sahaj / Sibling / Efforts / Courage)
    "younger sibling": 3, "younger brother": 3, "younger sister": 3, "courage": 3, "bravery": 3,
    "efforts": 3, "hobbies": 3, "short travel": 3, "writing": 3, "book": 3, "communication": 3, 
    "media": 3, "internet": 3, "data": 3, "marketing": 3, "ears": 3, "throat": 3, "arms": 3, "hands": 3,
    "chota bhai": 3, "choti behn": 3, "mehnat": 3, "sahas": 3, "yatra": 3, "likhna": 3,
    
    # 4th House (Sukh / Mother / Property / Vehicles)
    "mother": 4, "homeland": 4, "home": 4, "property": 4, "land": 4, "real estate": 4, 
    "vehicle": 4, "car": 4, "luxury": 4, "comforts": 4, "inner peace": 4, "chest": 4, 
    "lungs": 4, "heart": 4, "hospitality": 4, "hotel": 4, "school": 4,
    "maa": 4, "mummy": 4, "mata": 4, "ghar": 4, "gadi": 4, "sukh": 4, "zameen": 4,
    
    # 5th House (Santan / Children / Study / Love)
    "child": 5, "children": 5, "progeny": 5, "study": 5, "learning": 5, "education": 5, 
    "romance": 5, "love": 5, "crush": 5, "affair": 5, "creativity": 5, "intelligence": 5, 
    "wisdom": 5, "mantra": 5, "stomach": 5, "digestion": 5, "spinal cord": 5,
    "beta": 5, "beti": 5, "bachha": 5, "santan": 5, "padhai": 5, "pyar": 5, "buddhi": 5,
    
    # 6th House (Rog & Shatru / Disease / Enemy / Dispute / Job)
    "disease": 6, "illness": 6, "enemy": 6, "dispute": 6, "fight": 6, "litigation": 6, 
    "court case": 6, "debt": 6, "loan": 6, "job": 6, "service": 6, "servant": 6, "maternal uncle": 6,
    "kidney": 6, "vices": 6, "competition": 6, "exam": 6,
    "rog": 6, "shatru": 6, "dushman": 6, "jhagda": 6, "karz": 6, "naukri": 6, "mama": 6,
    
    # 7th House (Vivah / Spouse / Marriage / Business Partnership)
    "spouse": 7, "marriage": 7, "partner": 7, "partnership": 7, "husband": 7, "wife": 7, 
    "business": 7, "trading": 7, "retail": 7, "opposite gender": 7, "reproductive organs": 7,
    "pati": 7, "patni": 7, "shadi": 7, "vivah": 7, "vyapar": 7,
    
    # 8th House (Ayur & Mrityu / Secrets / Occult / In-laws / Pain)
    "secrets": 8, "mysteries": 8, "occult": 8, "astrology": 8, "in-laws": 8, "spouse wealth": 8, 
    "inheritance": 8, "pain": 8, "transformation": 8, "accident": 8, "surgery": 8, "death": 8, 
    "womb": 8, "lifespan": 8, "research": 8,
    "sasural": 8, "gupt": 8, "mrityu": 8, "dard": 8, "khoj": 8,
    
    # 9th House (Bhagya / Father / Mentor / Luck / Religion)
    "father": 9, "mentor": 9, "guru": 9, "teacher": 9, "luck": 9, "fortune": 9, 
    "religion": 9, "spirituality": 9, "pilgrimage": 9, "long travel": 9, "higher education": 9,
    "papa": 9, "pitaji": 9, "bhagya": 9, "dharma": 9, "dharmik": 9,
    
    # 10th House (Karma / Career / Status)
    "career": 10, "profession": 10, "work": 10, "job/career": 10, "karma": 10, "status": 10, 
    "fame": 10, "reputation": 10, "authority": 10, "government": 10, "mother-in-law": 10, "knees": 10,
    "kaam": 10, "karya": 10, "izzat": 10, "saas": 10,
    
    # 11th House (Labha / Income / Sibling / Gains / Bua)
    "income": 11, "gains": 11, "profit": 11, "elder sibling": 11, "elder brother": 11, 
    "elder sister": 11, "paternal uncle": 11, "paternal aunt": 11, "bua": 11, "chacha": 11, 
    "friends": 11, "desires": 11,
    "aamdani": 11, "labha": 11, "bada bhai": 11, "badi behn": 11,
    
    # 12th House (Vyaya / Losses / Foreign / Isolation)
    "losses": 12, "expenses": 12, "expenditure": 12, "foreign": 12, "abroad": 12, "videsh": 12,
    "isolation": 12, "confinement": 12, "sleep": 12, "bedroom": 12, "hospital": 12, "prison": 12, 
    "moksha": 12, "liberation": 12, "detachment": 12,
    "kharch": 12, "nuksan": 12, "neend": 12,
}

def identify_target_house_from_query(question: str) -> Optional[int]:
    """
    Analyzes the user's query text and dynamically returns the target house ID (1 to 12).
    If no specific relative or concept keyword matches, returns None to indicate
    the question is out-of-scope/unanswerable.
    """
    import re
    # Lowercase and normalize query characters
    clean_q = re.sub(r"[^a-zA-Z\s]", "", question.lower()).strip()
    words = clean_q.split()
    
    # 1. Check for multi-word phrases first
    for key, house in REPRESENTATION_KEYWORD_MAP.items():
        if " " in key and key in clean_q:
            return house
            
    # Generic pronouns that should not override more specific house keywords
    generic_pronouns = {"me", "myself", "my", "mera", "meri", "mujhe"}
    
    # 2. Check for single-word tokens
    matches = []
    for word in words:
        if word in REPRESENTATION_KEYWORD_MAP:
            matches.append((word, REPRESENTATION_KEYWORD_MAP[word]))
            
    if not matches:
        return None
        
    # Return the first match that is not a generic pronoun
    for word, house in matches:
        if word not in generic_pronouns:
            return house
            
    # Fallback to the first generic pronoun match (typically House 1)
    return matches[0][1]


