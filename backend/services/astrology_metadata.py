# astrology_metadata.py
# AstroCare AI — Astrological Expert System Metadata Engine
# Optimized for high-speed, highly accurate LLM (Gemini) parsing

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
