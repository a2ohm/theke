def parse_robinson(morph):
    subMorph = morph.split('-')
    return [wordClasses.get(subMorph[0], lambda x: "inconnu")(subMorph[1:])]

mood = {
    'I': "indicatif",
    'M': "impératif",
    'N': "infinitif",
    'O': "optatif",
    'P': "participe",
    'S': "subjonctif",
}

tence = {
    '2A': "aoriste second",
    'A': "aoriste",
    'F': "futur",
    'I': "imparfait",
    'L': "plus-que-parfait",
    'P': "présent",
    'R': "parfait",
    'X': "impératif adverbial",
}

voice = {
    'A': "actif",
    'M': "moyen",
    'P': "passif",
}

def parse_robinson_verb(subMorph):
    # submorph = [tence / voice / mood][person / number]
    # submorph = [tence / voice / mood][case / number / gender]

    tvm = subMorph[0]
    tvmAnalysed = "{} {} {}".format(
        mood.get(tvm[-1], '?'),
        tence.get(tvm[:-2], '?'),
        voice.get(tvm[-2], '?'))

    return "verbe ({})".format(tvmAnalysed)

wordClasses = {
    'A': lambda x: "adjectif",
    'C': lambda x: "pronom réciproque",
    'D': lambda x: "pronom démonstratif",
    'F': lambda x: "pronom réfléchit",
    'I': lambda x: "pronom interrogatif",
    'K': lambda x: "pronom corrélatif",
    'N': lambda x: "nom",
    'P': lambda x: "pronom personnel",
    'Q': lambda x: "pronom corrélatif ou interrogatif",
    'R': lambda x: "pronom relatif",
    'S': lambda x: "pronom possessif",
    'T': lambda x: "article défini",
    'V': parse_robinson_verb,
    'X': lambda x: "pronom indéfini",
}
