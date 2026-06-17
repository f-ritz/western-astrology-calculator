"""
Interpretations database - EASY TO EDIT by the astrologer user.

Signs use 3-letter keys ('Ari' etc) to match kerykeion output.
Use SIGN_FULL to convert to full names for display.

Add your own research text here. The code falls back gracefully.
"""

SIGN_FULL = {
    'Ari': 'Aries', 'Tau': 'Taurus', 'Gem': 'Gemini',
    'Can': 'Cancer', 'Leo': 'Leo', 'Vir': 'Virgo',
    'Lib': 'Libra', 'Sco': 'Scorpio', 'Sag': 'Sagittarius',
    'Cap': 'Capricorn', 'Aqu': 'Aquarius', 'Pis': 'Pisces'
}

PLANET_SIGN_INTERPS = {
    "Sun": {
        "Ari": "Aries Suns are direct, energetic pioneers who live in the moment and charge forward with courage and independence.",
        "Tau": "Taurus Suns are steady, sensual, and security-oriented. They work hard for comfort and value reliability and the good things in life.",
        "Gem": "Gemini Suns are curious communicators who collect and share information with wit and versatility.",
        "Can": "Cancer Suns are protective, emotional, and family-rooted. They lead with feeling and create security for themselves and others.",
        "Leo": "Leo Suns shine with natural leadership, warmth, creativity, and a regal sense of self-expression.",
        "Vir": "Virgo Suns are practical, analytical, and service-minded. They find purpose through useful work and attention to detail.",
        "Lib": "Libra Suns seek balance, harmony, and partnership. They express through diplomacy, beauty, and fair relationships.",
        "Sco": "Scorpio Suns are intense, transformative, and deeply perceptive. They wield power and probe life's mysteries.",
        "Sag": "Sagittarius Suns are optimistic explorers and truth-seekers who expand through philosophy, travel, and big ideas.",
        "Cap": "Capricorn Suns are ambitious, disciplined builders who achieve through responsibility and long-term mastery.",
        "Aqu": "Aquarius Suns are innovative humanitarians who express through originality, groups, and progressive ideals.",
        "Pis": "Pisces Suns are compassionate, imaginative, and spiritually attuned. They lead through empathy and creative dissolution of boundaries.",
    },
    "Moon": {
        "Ari": "Moon in Aries reacts quickly and directly with fiery independence and a need for immediate emotional action.",
        "Tau": "Moon in Taurus seeks emotional security through comfort, routine, and the reliable pleasures of the senses.",
        "Gem": "Moon in Gemini needs mental stimulation and variety to feel emotionally safe; feelings are expressed through words and curiosity.",
        "Can": "Moon in Cancer is deeply nurturing, protective, and attached to home and emotional history.",
        "Leo": "Moon in Leo needs recognition, warmth, and creative self-expression to feel emotionally fulfilled.",
        "Vir": "Moon in Virgo finds emotional security in order, usefulness, and taking care of details and others.",
        "Lib": "Moon in Libra seeks emotional balance through relationships, beauty, and fair, harmonious interactions.",
        "Sco": "Moon in Scorpio experiences emotions intensely and privately, with a need for deep trust and transformation.",
        "Sag": "Moon in Sagittarius needs freedom, adventure, and meaning to feel emotionally expansive and optimistic.",
        "Cap": "Moon in Capricorn finds security through achievement, structure, and emotional self-reliance.",
        "Aqu": "Moon in Aquarius needs intellectual freedom, friendship, and humanitarian connection for emotional well-being.",
        "Pis": "Moon in Pisces is empathic, dreamy, and spiritually sensitive; emotions flow and merge with the environment.",
    },
    # Add more planets (Mercury, Venus...) here. User can expand easily.
}

PLANET_HOUSE_INTERPS = {
    "Sun": {
        1: "Your identity is front and center. Life forces you to become unmistakably yourself.",
        2: "Self-worth and material security are central themes.",
        3: "Communication, learning, and connecting with your immediate environment are key.",
        4: "Home, family, roots, and emotional foundations are where your light shines.",
        5: "Creative self-expression, romance, and joy are your lifeblood.",
        6: "Work, service, health, and daily routines are the stage for your growth.",
        7: "Partnerships and one-to-one relationships are the mirror for your development.",
        8: "Transformation, shared resources, intimacy, and the mysteries of life are your path.",
        9: "Travel, philosophy, higher learning, and publishing expand your horizons.",
        10: "Career, reputation, and public role are where your light shines brightest.",
        11: "Friends, groups, communities, and humanitarian causes are central.",
        12: "The subconscious, spirituality, solitude, and behind-the-scenes work complete the cycle.",
    },
}

ASPECT_GENERAL = {
    "conjunction": "The energies of the two planets are united and act together. Powerful blending.",
    "sextile": "A harmonious aspect that suggests opportunity and ease. Requires some effort to activate.",
    "square": "A tense, dynamic aspect that creates friction and challenges. Forces growth.",
    "trine": "A very harmonious flow. The planets support each other naturally with little effort.",
    "opposition": "Polarity and awareness through relationship. Requires balance and integration.",
    "quincunx": "An awkward adjustment aspect. The planets require ongoing adaptation.",
}

def get_planet_sign_interpretation(planet_name: str, sign: str) -> str:
    key = sign[:3] if sign else ""
    planet_dict = PLANET_SIGN_INTERPS.get(planet_name, {})
    if key in planet_dict:
        return planet_dict[key]
    full = SIGN_FULL.get(key, sign)
    return f"{planet_name} in {full} activates {planet_name.lower()}-ruled qualities through a {full.lower()} lens."

def get_planet_house_interpretation(planet_name: str, house: int) -> str:
    if planet_name in PLANET_HOUSE_INTERPS and house in PLANET_HOUSE_INTERPS[planet_name]:
        return PLANET_HOUSE_INTERPS[planet_name][house]
    return f"In the {house}th house, {planet_name} directs its energy toward matters of that house."

def get_aspect_interpretation(p1: str, p2: str, aspect_type: str) -> str:
    return ASPECT_GENERAL.get(aspect_type.lower(), f"The {aspect_type} between {p1} and {p2} combines their energies.")

def get_retrograde_note(planet_name: str) -> str:
    notes = {
        "Mercury": "Mercury retrograde in the natal chart often indicates a person who thinks deeply and may have a non-linear style of learning and communicating.",
        "Venus": "Venus retrograde suggests a need to review values, relationships, and self-worth from within.",
        "Mars": "Mars retrograde can indicate internalized drive or anger that needs conscious direction.",
    }
    return notes.get(planet_name, f"{planet_name} retrograde suggests the energy of this planet is turned inward or needs special conscious integration.")

# Ascendant interpretations (3-letter keys)
ASC_SIGN_INTERPS = {
    'Ari': "People with Aries Ascendants are direct and quick. Their first instinct is to do, rather than think. They have a youthful, direct manner.",
    'Tau': "Slow, steady, and capable. Taurus Ascendant natives have tremendous stamina and radiate stability.",
    'Gem': "Gemini Rising see the world as a place to learn. Curious, restless, quick in expression, and clever.",
    'Can': "Cancer Ascendant people come across as gentle and familiar. Sensitive to environment, they protect themselves and have a nurturing quality.",
    'Leo': "Leo Rising project generosity, pride, and drama. They have natural flair and carry themselves with confidence and warmth.",
    'Vir': "Virgo Ascendant appear modest, analytical, and helpful. They notice details and strive for precision and service.",
    'Lib': "Libra Rising have natural charm and grace. Diplomatic, fair-minded, sociable, with a desire for harmony.",
    'Sco': "Scorpio Rising have an intense, magnetic, private presence. Perceptive and powerful, with strong willpower.",
    'Sag': "Sagittarius Rising are open, optimistic, and adventurous. Friendly, philosophical, freedom-loving.",
    'Cap': "Capricorn Rising project seriousness, ambition, and competence. Responsible, reserved, goal-oriented.",
    'Aqu': "Aquarius Rising have a unique, independent, humanitarian vibe. Intellectual, unconventional, forward-thinking.",
    'Pis': "Pisces Rising have a soft, dreamy, compassionate presence. Gentle, intuitive, empathetic and adaptable.",
}

# Midheaven interpretations (3-letter keys)
MC_SIGN_INTERPS = {
    'Ari': "You can be a pioneer in career and life path. Independent, visionary. Value freedom and new challenges in work.",
    'Tau': "Seek stability and predictability professionally. Hard worker, resourceful, common sense. Value security and quality.",
    'Gem': "Fulfilled by expressing, diversifying, teaching, communicating. Often multiple professions or versatile roles.",
    'Can': "Warmth and care show in what you do. Take time to come into your own. Strong intuition about public needs.",
    'Leo': "Need to feel in charge. Natural leader with heart and personality in career. Stand out and shine.",
    'Vir': "Orderly, efficient, humble image. Strong work ethic and duty. Analytical and observant. Service-oriented.",
    'Lib': "Weigh decisions carefully, seek middle road. Gracious, fair, diplomatic. Team player and mediator.",
    'Sco': "Determined, passionate, intuitive in career. Intense image. Forge own path; dramatic shifts possible.",
    'Sag': "Drawn to freedom, exploration, teaching, publishing. Seek meaning and adventure. Optimistic big-picture view.",
    'Cap': "Strong responsibility and ambition. Willing to work hard and climb steadily. Competent, authoritative image.",
    'Aqu': "Innovative, humanitarian goals. Work that makes a difference or involves groups/technology/future. Unconventional path.",
    'Pis': "Drawn to compassionate, artistic, healing, spiritual work. Help others or creativity. Strong intuition; some fluidity.",
}

def get_ascendant_interpretation(sign: str) -> str:
    key = sign[:3] if sign else ''
    if key in ASC_SIGN_INTERPS:
        return ASC_SIGN_INTERPS[key]
    for k, full in SIGN_FULL.items():
        if full.lower() == (sign or '').lower():
            return ASC_SIGN_INTERPS.get(k, '')
    return 'The Ascendant in this sign colors your outward personality and first impressions.'

def get_midheaven_interpretation(sign: str) -> str:
    key = sign[:3] if sign else ''
    if key in MC_SIGN_INTERPS:
        return MC_SIGN_INTERPS[key]
    for k, full in SIGN_FULL.items():
        if full.lower() == (sign or '').lower():
            return MC_SIGN_INTERPS.get(k, '')
    return 'The Midheaven in this sign influences your career path, public image, and life direction.'