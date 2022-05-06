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

mode = {
    'p': "accompli",
    'i': "inaccompli",
    'w': "consécutif",
    'r': "participe actif",
    's': "participe passif",
}

person = {
    '1': "1e personne",
    '2': "2e personne",
    '3': "3e personne",
}

number = {
    's': "singulier",
    'p': "pluriel",
}

gender = {
    'm': "masculin",
    'f': "féminin",
    'b': "masc. et fém.",
    'c': "commune",
}


noun_type = {
    'c': "nom commun",
    'g': "gentilé"
}

noun_form = {
    's': "sing.",
    'p': "pl.",
    'd': "duel"
}

state = {
    'c': "const.",
    'a': "abs."
}

def parse_oshm_verb(subMorph):
    return "verbe ({} {} {} {} {})".format(
        tences.get(subMorph[1], '?'),
        mode.get(subMorph[2], '?'),
        person.get(subMorph[3], '?'),
        gender.get(subMorph[4], '?'),
        number.get(subMorph[5], '?'),
        )

def parse_oshm_noun(subMorph):
    pattern_noun = re.compile(r'N(p)|N((?P<type>g|c)(?P<genre>m|f|b)(?P<form>s|p|d)(?P<state>c|a))')
    match_noun = pattern_noun.match(subMorph)

    if match_noun is not None:
        if match_noun.group(2) is None:
            return "nom propre"
        else:
            return "{} {} {} (état {})".format(
                noun_type[match_noun.group("type")],
                gender[match_noun.group("genre")],
                noun_form[match_noun.group("form")],
                state[match_noun.group("state")])

    return "nom"

def parse_oshm_suffix(subMorph):
    return "suffixe ({} {} {})".format(
        person.get(subMorph[2], '?'),
        gender.get(subMorph[3], '?'),
        number.get(subMorph[4], '?'),
        )

def parse_oshm_adjective(subMorph):
    return "adjectif ({} {} {})".format(
        gender.get(subMorph[2], '?'),
        number.get(subMorph[3], '?'),
        state.get(subMorph[4], '?'),
        )

wordClasses = {
    'A': parse_oshm_adjective,
    'C': lambda x: "conjonction",
    'D': lambda x: "adverbe",
    'N': parse_oshm_noun,
    'P': lambda x: "pronom démonstratif",
    'R': lambda x: "préposition",
    'S': parse_oshm_suffix,
    'T': lambda x: "particule",
    'V': parse_oshm_verb,
}