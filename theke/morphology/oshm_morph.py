import re

def parse_oshm(morph):
    analysis = []

    for subMorph in morph[1:].split('_'):
        analysis.append(wordClasses.get(subMorph[0], lambda x: "inconnu")(subMorph))
    
    return analysis

tences = {
    'D': "nithpael (?)",
    'H': "hof'al",
    'K': "pulal (?)",
    'L': "polpal (?)",
    'M': "poal (?)",
    'N': "nif'al",
    'O': "polal (?)",
    'P': "pu'al",
    'Q': "qal",
    'c': "tiphil (?)",
    'f': "hithpalpel",
    'h': "hif'il",
    'i': "pilel (?)",
    'j': "pealal (?)",
    'k': "palel (?)",
    'l': "pilpel (?)",
    'm': "poel (?)",
    'o': "polel (?)",
    'p': "pi'el",
    'q': "qal",
    'r': "hithpolel (?)",
    't': "hithpael (?)",
    'u': "hothpaal (?)",
    'v': "hishthaphel (?)",
    'z': "hitpoel (?)",
}

def parse_oshm_verb(subMorph):
    return "verbe ({})".format(tences.get(subMorph[1], '?'))

noun_type = {
    'c': "nom commun",
    'g': "gentilé"
}

noun_genre = {
    'm': "masc.",
    'f': "fém.", 
    'b': "masc. et fém."
}

noun_form = {
    's': "sing.",
    'p': "pl.",
    'd': "duel"
}

noun_state = {
    'c': "const.",
    'a': "abs."
}

def parse_oshm_noun(subMorph):
    pattern_noun = re.compile(r'N(p)|N((?P<type>g|c)(?P<genre>m|f|b)(?P<form>s|p|d)(?P<state>c|a))')
    match_noun = pattern_noun.match(subMorph)

    if match_noun is not None:
        if match_noun.group(2) is None:
            return "nom propre"
        else:
            return "{} {} {} (état {})".format(
                noun_type[match_noun.group("type")],
                noun_genre[match_noun.group("genre")],
                noun_form[match_noun.group("form")],
                noun_state[match_noun.group("state")])

    return "nom"

wordClasses = {
    'A': lambda x: "adjectif",
    'C': lambda x: "conjonction",
    'D': lambda x: "adverbe",
    'N': parse_oshm_noun,
    'P': lambda x: "pronom démonstratif",
    'R': lambda x: "préposition",
    'S': lambda x: "suffixe",
    'T': lambda x: "particule",
    'V': parse_oshm_verb,
}