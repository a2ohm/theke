def parse_oshm(morph):
    analysis = []

    for subMorph in morph[1:].split('_'):
        analysis.append(wordClasses.get(subMorph[0], lambda x: "inconnu")(subMorph))
    
    return analysis

def parse_oshm_verb(subMorph):
    return "verbe ({})".format(tences.get(subMorph[1], '?'))

wordClasses = {
    'A': lambda x: "adjectif",
    'C': lambda x: "conjonction",
    'D': lambda x: "adverbe",
    'N': lambda x: "nom",
    'P': lambda x: "pronom démonstratif",
    'R': lambda x: "préposition",
    'S': lambda x: "suffixe",
    'T': lambda x: "particule",
    'V': parse_oshm_verb,
}

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