"""
Fact Verifier and Relational Assertion Checker for Fake News Detection System.
Prevents bag-of-words false positives where distinct entities interacting in news
(e.g., 'PM Modi meets TN CM Stalin') are mistaken as verifying a false identity
claim (e.g., 'PM Modi is the CM of TN').

Includes:
1. Canonical public office / dignitary verification (India & Global)
2. Identity and role assertion contradiction detection ('X is Y of Z')
3. Cross-entity interaction vs. identity entailment analysis
4. Multilingual support (English, Hindi, Telugu, Tamil, etc.)
"""
import re
from typing import Dict, Any, Optional, Tuple, List


# Known Indian State Leadership & Public Dignitaries
INDIAN_STATES_DATA = {
    "tamil_nadu": {
        "names": ["tamil nadu", "tamilnadu", "tn", "chennai", "தமிழ்நாடு", "తమిళనాడు", "तमिलनाडु"],
        "cm": "M.K. Stalin",
        "cm_party": "DMK",
        "aliases": ["stalin", "m.k. stalin", "m k stalin", "vijay", "edappadi palaniswami", "eps"]
    },
    "andhra_pradesh": {
        "names": ["andhra pradesh", "andhra", "ap", "amaravati", "ఆంధ్రప్రదేశ్", "ఆంధ్ర", "आंध्र प्रदेश"],
        "cm": "N. Chandrababu Naidu",
        "cm_party": "TDP",
        "aliases": ["chandrababu naidu", "cbn", "naidu", "ys jagan", "jagan"]
    },
    "telangana": {
        "names": ["telangana", "tg", "ts", "hyderabad", "తెలంగాణ", "तेलंगाना"],
        "cm": "A. Revanth Reddy",
        "cm_party": "Congress",
        "aliases": ["revanth reddy", "revanth", "kcr", "k. chandrashekar rao"]
    },
    "karnataka": {
        "names": ["karnataka", "ka", "bengaluru", "bangalore", "ಕರ್ನಾಟಕ", "కర్ణాటక", "कर्नाटक"],
        "cm": "Siddaramaiah",
        "cm_party": "Congress",
        "aliases": ["siddaramaiah", "d.k. shivakumar", "bommai"]
    },
    "kerala": {
        "names": ["kerala", "kl", "thiruvananthapuram", "கேரளா", "కేరళ", "केरल"],
        "cm": "Pinarayi Vijayan",
        "cm_party": "CPI(M)",
        "aliases": ["pinarayi vijayan", "pinarayi"]
    },
    "uttar_pradesh": {
        "names": ["uttar pradesh", "up", "lucknow", "उत्तर प्रदेश", "ఉత్తర ప్రదేశ్"],
        "cm": "Yogi Adityanath",
        "cm_party": "BJP",
        "aliases": ["yogi adityanath", "yogi", "adityanath", "akhilesh yadav"]
    },
    "west_bengal": {
        "names": ["west bengal", "wb", "bengal", "kolkata", "পশ্চিমবঙ্গ", "पश्चिम बंगाल", "పశ్చిమ బెంగాల్"],
        "cm": "Mamata Banerjee",
        "cm_party": "TMC",
        "aliases": ["mamata banerjee", "mamata", "didi"]
    },
    "maharashtra": {
        "names": ["maharashtra", "mh", "mumbai", "महाराष्ट्र", "మహారాష్ట్ర"],
        "cm": "Devendra Fadnavis",
        "cm_party": "BJP",
        "aliases": ["devendra fadnavis", "eknath shinde", "fadnavis", "shinde", "uddhav thackeray"]
    },
    "delhi": {
        "names": ["delhi", "nct of delhi", "दिल्ली", "ఢిల్లీ"],
        "cm": "Atishi",
        "cm_party": "AAP",
        "aliases": ["atishi", "arvind kejriwal", "kejriwal"]
    },
    "bihar": {
        "names": ["bihar", "patna", "बिहार", "బీహార్"],
        "cm": "Nitish Kumar",
        "cm_party": "JDU",
        "aliases": ["nitish kumar", "nitish", "tejashwi yadav"]
    },
    "gujarat": {
        "names": ["gujarat", "gandhinagar", "गुजरात", "గుజరాత్"],
        "cm": "Bhupendrabhai Patel",
        "cm_party": "BJP",
        "aliases": ["bhupendrabhai patel", "bhupendra patel"]
    },
    "odisha": {
        "names": ["odisha", "orissa", "bhubaneswar", "ओडिशा", "ఒడిశా"],
        "cm": "Mohan Charan Majhi",
        "cm_party": "BJP",
        "aliases": ["mohan charan majhi", "naveen patnaik"]
    },
    "punjab": {
        "names": ["punjab", "chandigarh", "पंजाब", "పంజాబ్"],
        "cm": "Bhagwant Mann",
        "cm_party": "AAP",
        "aliases": ["bhagwant mann", "mann"]
    },
    "rajasthan": {
        "names": ["rajasthan", "jaipur", "राजस्थान", "రాజస్థాన్"],
        "cm": "Bhajan Lal Sharma",
        "cm_party": "BJP",
        "aliases": ["bhajan lal sharma", "ashok gehlot"]
    },
    "madhya_pradesh": {
        "names": ["madhya pradesh", "mp", "bhopal", "मध्य प्रदेश", "మధ్యప్రదేశ్"],
        "cm": "Mohan Yadav",
        "cm_party": "BJP",
        "aliases": ["mohan yadav", "shivraj singh chouhan"]
    },
    "assam": {
        "names": ["assam", "dispur", "असम", "అసోం"],
        "cm": "Himanta Biswa Sarma",
        "cm_party": "BJP",
        "aliases": ["himanta biswa sarma", "himanta"]
    }
}


# Known National & Global Top Offices
NATIONAL_OFFICES = {
    "pm_india": {
        "title": "Prime Minister of India",
        "title_aliases": ["pm of india", "prime minister of india", "pm", "prime minister", "pradhan mantri", "భారత ప్రధాని", "భారత ప్రధానమంత్రి", "प्रधानमंत्री", "இந்திய பிரதமர்"],
        "holder": "Narendra Modi",
        "aliases": ["narendra modi", "modi", "namo", "మోదీ", "मोदी", "மோடி"]
    },
    "president_india": {
        "title": "President of India",
        "title_aliases": ["president of india", "rashtrapati", "president", "భారత రాష్ట్రపతి", "राष्ट्रपति", "இந்திய ஜனாதிபதி"],
        "holder": "Droupadi Murmu",
        "aliases": ["droupadi murmu", "draupadi murmu", "murmu", "ద్రౌపది ముర్ము", "द्रौपदी मुर्मू"]
    },
    "president_usa": {
        "title": "President of the United States",
        "title_aliases": ["president of usa", "president of america", "president of us", "potus", "us president", "american president"],
        "holder": "Donald Trump",
        "aliases": ["donald trump", "trump", "joe biden", "biden", "ట్రంప్", "ट्रम्प"]
    }
}


def check_canonical_role_mismatch(text: str) -> Optional[Dict[str, Any]]:
    """Check if the statement makes an impossible or contradictory role claim.
    
    Examples:
    - 'PM Modi is the CM of TN' -> FALSE (Modi is PM of India, not CM of TN)
    - 'Rahul Gandhi is Prime Minister of India' -> FALSE
    - 'Virat Kohli is President of India' -> FALSE
    """
    cleaned = text.lower().strip()
    
    # Check for keywords indicating Chief Minister
    cm_indicators = [
        "cm", "chief minister", "mukhyamantri", "mukhya mantri",
        "ముఖ్యమంత్రి", "సీఎం", "മുഖ്യമന്ത്രി", "முதல்வர்", "முதலமைச்சர்", "సి.ఎం"
    ]
    has_cm = any(re.search(r'\b' + re.escape(c) + r'\b', cleaned) or c in cleaned for c in cm_indicators)
    
    # Check for Modi mentions
    modi_indicators = ["modi", "narendra modi", "namo", "మోదీ", "మోడి", "मोदी", "மோடி"]
    has_modi = any(m in cleaned for m in modi_indicators)
    
    # 1. SPECIAL CASE: Claiming Modi is the CM of any state
    if has_modi and has_cm:
        for state_key, sdata in INDIAN_STATES_DATA.items():
            state_matched = False
            matched_state_name = ""
            for sname in sdata["names"]:
                if re.search(r'\b' + re.escape(sname) + r'\b', cleaned) or sname in cleaned:
                    state_matched = True
                    matched_state_name = sdata["names"][0].title()
                    break
                    
            if state_matched:
                actual_cm = sdata["cm"]
                return {
                    "is_contradiction": True,
                    "claimed_entity": "Narendra Modi",
                    "claimed_role": f"Chief Minister of {matched_state_name}",
                    "actual_role": "Prime Minister of India",
                    "actual_office_holder": actual_cm,
                    "explanation": (
                        f"Factually False: Narendra Modi is the Prime Minister of India, "
                        f"NOT the Chief Minister of {matched_state_name}. "
                        f"The current Chief Minister of {matched_state_name} is {actual_cm}."
                    )
                }
                
    # 2. General State CM Mismatch: claiming "<Person> is the CM of <State>" or "<State> CM is <Person>"
    if has_cm:
        for state_key, sdata in INDIAN_STATES_DATA.items():
            state_matched = False
            for sname in sdata["names"]:
                if re.search(r'\b' + re.escape(sname) + r'\b', cleaned) or sname in cleaned:
                    state_matched = True
                    break
                    
            if state_matched:
                claimed_person = None
                
                # Forward pattern: "<person> is [the] cm"
                pattern_fwd = r'([a-z\s]+?)\s+(?:is|became|elected|sworn in as|serving as)\s+(?:the\s+)?(?:cm|chief minister|mukhyamantri)\b'
                m_fwd = re.search(pattern_fwd, cleaned)
                if m_fwd:
                    claimed_person = m_fwd.group(1).strip()
                else:
                    # Reverse pattern: "<state> cm is <person>" or "cm of <state> is <person>"
                    # e.g., "ap cm is rahul gandhi" or "cm of ap is rahul gandhi"
                    pattern_rev = r'\b(?:(?:' + '|'.join(re.escape(sn) for sn in sdata["names"]) + r')\s+(?:cm|chief minister|mukhyamantri)|(?:cm|chief minister|mukhyamantri)\s+(?:of\s+)?(?:' + '|'.join(re.escape(sn) for sn in sdata["names"]) + r'))\s+(?:is|became|elected|now|was)\s+([a-z\s]+?)(?:[.,;!]|$)'
                    m_rev = re.search(pattern_rev, cleaned)
                    if m_rev:
                        claimed_person = m_rev.group(1).strip()
                
                if claimed_person:
                    # Clean filler words
                    claimed_person = re.sub(r'^(that|which|who|if|whether|says|claims|breaking|alert|the|a|an)\s+', '', claimed_person).strip()
                    # If person is not in aliases for this state
                    if claimed_person and len(claimed_person) > 2 and not any(alias in claimed_person for alias in sdata["aliases"]):
                        return {
                            "is_contradiction": True,
                            "claimed_entity": claimed_person.title(),
                            "claimed_role": f"Chief Minister of {sdata['names'][0].title()}",
                            "actual_office_holder": sdata["cm"],
                            "explanation": (
                                f"Factually False: {claimed_person.title()} is NOT the Chief Minister of {sdata['names'][0].title()}. "
                                f"The position is held by {sdata['cm']}."
                            )
                        }

    # 3. National Dignitary Mismatches (PM of India, President of India, etc.)
    # Supports both "<Person> is the <Title>" and "<Title> is <Person>"
    sorted_offices = []
    for office_key, odata in NATIONAL_OFFICES.items():
        for ta in odata["title_aliases"]:
            sorted_offices.append((len(ta), ta, office_key, odata))
    sorted_offices.sort(key=lambda x: x[0], reverse=True)
    
    for _, ta, office_key, odata in sorted_offices:
        claimed_person = None
        # Forward pattern: "<person> is [the] <title>"
        pattern_fwd = r'([a-z\s]+?)\s+(?:is|became|elected|appointed|sworn in as)\s+(?:the\s+)?' + re.escape(ta) + r'\b'
        m_fwd = re.search(pattern_fwd, cleaned)
        if m_fwd:
            claimed_person = m_fwd.group(1).strip()
        else:
            # Reverse pattern: "<title> is <person>"
            pattern_rev = r'\b' + re.escape(ta) + r'\s+(?:is|became|elected|appointed|now|was)\s+([a-z\s]+?)(?:[.,;!]|$)'
            m_rev = re.search(pattern_rev, cleaned)
            if m_rev:
                claimed_person = m_rev.group(1).strip()
                
        if claimed_person:
            claimed_person = re.sub(r'^(that|which|who|if|whether|says|claims|breaking|the|a|an)\s+', '', claimed_person).strip()
            if claimed_person and len(claimed_person) > 2 and not any(alias in claimed_person for alias in odata["aliases"]):
                return {
                    "is_contradiction": True,
                    "claimed_entity": claimed_person.title(),
                    "claimed_role": odata["title"],
                    "actual_office_holder": odata["holder"],
                    "explanation": (
                        f"Factually False: {claimed_person.title()} is NOT the {odata['title']}. "
                        f"The position is held by {odata['holder']}."
                    )
                }

    return None


def analyze_headline_entailment(claim_text: str, matched_headlines: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Analyze if the headlines returned by Google News actually ENTAIL (support) the claim
    or if they represent an INTERACTION between two distinct entities that CONTRADICTS the claim.
    
    Example:
    Claim: 'PM Modi is the CM of TN'
    Headline: 'PM Modi and CM Vijay commit themselves to working together for Tamil Nadu'
    
    Headline proves PM Modi is NOT CM Vijay. They are two distinct individuals!
    
    Returns:
        (is_contradicted, explanation)
    """
    cleaned_claim = claim_text.lower()
    
    # Check if claim asserts X is Y
    is_identity_claim = bool(re.search(r'\b\w+\s+is\s+(?:the\s+)?\w+\b', cleaned_claim))
    has_pm = bool(re.search(r'\bpm\b', cleaned_claim) or "prime minister" in cleaned_claim)
    has_cm = bool(re.search(r'\bcm\b', cleaned_claim) or "chief minister" in cleaned_claim)
    
    if not (is_identity_claim or (has_pm and has_cm)):
        return False, ""
        
    if not matched_headlines:
        return False, ""
        
    # Analyze matched headlines
    interaction_patterns = [
        r'\band\s+cm\b', r'\bwith\s+cm\b', r'\bto\s+cm\b', r'\btells\s+cm\b',
        r'\bgreets\s+cm\b', r'\bwrites\s+to\s+pm\b', r'\btells\s+pm\b',
        r'\burges\s+pm\b', r'\bmeets\s+pm\b', r'\bshares\s+dais\s+with\b',
        r'\balong\s+with\s+(?:tn\s+)?cm\b', r'\brides\s+along\s+with\b',
        r'\bwork\s+with\s+cm\b', r'\bletter\s+to\s+pm\b', r'\bwith\s+pm\b',
        r'\bmeeting\s+with\s+pm\b', r'\bgreets\s+people\b', r'\bshares\s+stage\b'
    ]
    
    interaction_count = 0
    distinct_cm_names = set()
    
    for h in matched_headlines:
        title = h.get("title", "").lower() if isinstance(h, dict) else str(h).lower()
        
        # Check for interaction indicators
        for pattern in interaction_patterns:
            if re.search(pattern, title):
                interaction_count += 1
                break
                
        # Look for names attached to CM (e.g. "CM Vijay", "CM Stalin", "TN CM Vijay")
        cm_matches = re.findall(r'\bcm\s+([a-z]+)\b', title)
        for name in cm_matches:
            if name not in ["modi", "of", "in", "and", "is", "says", "the", "for", "to"]:
                distinct_cm_names.add(name.title())
                
    # If the user claimed an identity (like PM Modi is CM), but the headlines consistently show
    # that PM Modi is interacting with a separate Chief Minister (Vijay or Stalin):
    if interaction_count >= 1 and distinct_cm_names:
        names_str = ", ".join(sorted(distinct_cm_names))
        return True, (
            f"Factual Refutation: The verified news headlines report an interaction "
            f"between Prime Minister Narendra Modi and the Chief Minister ({names_str}) "
            f"as two separate individuals, conclusively refuting the claim that PM Modi is the CM."
        )
        
    return False, ""
