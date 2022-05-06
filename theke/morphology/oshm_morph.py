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
    'w': "inaccompli consécutif",
    'r': "participe actif",
    's': "participe passif",
    'q': "accompli consécutif",
    'h': "cohortatif",
    'j': "jussif",
    'v': "impératif",
    'a': "infinitif absolu",
    'c': "infinitif construit",
}

person = {
    '1': "1e personne",
    '2': "2e personne",
    '3': "3e personne",
}

number = {
    's': "singulier",
    'p': "pluriel",
    'd': "duel",
}

gender = {
    'm': "masculin",
    'f': "féminin",
    'b': "masc. et fém.",
    'c': "commune",
}


noun_type = {
    'c': "nom commun",
    'g': "gentilé",
    'p': "nom propre",
}

state = {
    'c': "const.",
    'a': "abs.",
    'd': "déterminé"
}

particle = {
    'a': "affirmative",
    'd': "article défini",
    'e': "exhortative",
    'i': "interrogative",
    'j': "interjection",
    'm': "démonstrative",
    'n': "négation",
    'o': "complément d'objet direct",
    'r': "relative",
}

adjective = {
    'a': "simple",
    'c': "nombre cardinal",
    'g': "gentilé",
    'o': "nombre ordinal",
}

pronoun = {
    'd': "démonstratif",
    'f': "indéfini",
    'i': "interrogatif",
    'p': "personnel",
    'r': "relatif",
}

def parse_oshm_verb(subMorph):
    if subMorph[2] in ('r', 's'):   #participles don't have a person but they have a state
        return "verbe ({} {} {} {} {})".format(
            tences.get(subMorph[1], '?'),
            mode.get(subMorph[2], '?'),
            gender.get(subMorph[3], '?'),
            number.get(subMorph[4], '?'),
            state.get(subMorph[5], '?')
            )
    else:
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
                number[match_noun.group("form")],
                state[match_noun.group("state")])

    return "nom"

def parse_oshm_suffix(subMorph):
    return "suffixe ({} {} {})".format(
        person.get(subMorph[2], '?'),
        gender.get(subMorph[3], '?'),
        number.get(subMorph[4], '?'),
        )

def parse_oshm_adjective(subMorph):
    return "adjectif ({} {} {} {})".format(
        adjective.get(subMorph[1], '?'),
        gender.get(subMorph[2], '?'),
        number.get(subMorph[3], '?'),
        state.get(subMorph[4], '?'),
        )

def parse_oshm_particle(subMorph):
    return "particule ({})".format(
        particle.get(subMorph[1], '?'),
        )

def parse_oshm_pronoun(subMorph):
    return "pronom ({})".format(
        pronoun.get(subMorph[1], '?'),
        )

wordClasses = {
    'A': parse_oshm_adjective,
    'C': lambda x: "conjonction",
    'D': lambda x: "adverbe",
    'N': parse_oshm_noun,
    'P': parse_oshm_pronoun,
    'R': lambda x: "préposition (article défini)",
    'S': parse_oshm_suffix,
    'T': parse_oshm_particle,
    'V': parse_oshm_verb,
}