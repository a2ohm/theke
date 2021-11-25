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
    'N': "moyen ou passif déponent",
}

person = {
    '1': "1e personne",
    '2': "2e personne",
    '3': "3e personne",
}

number = {
    'S': "singulier",
    'P': "pluriel",
}

case = {
    'N': "nominatif",
    'V': "vocatif",
    'A': "accusatif",
    'G': "génitif",
    'D': "datif",
}

gender = {
    'M': "masculin",
    'F': "féminin",
    'N': "neutre",
}

def parse_robinson_verb(subMorph):
    # submorph = [tence / voice / mood]
    # submorph = [tence / voice / mood][person / number]
    # submorph = [tence / voice / mood][case / number / gender]

    tvm = subMorph[0]
    tvmAnalysed = "{} {} {}".format(
        mood.get(tvm[-1], '?'),
        tence.get(tvm[:-2], '?'),
        voice.get(tvm[-2], '?')
    )

    if len(subMorph) == 2:
        end = subMorph[1]
        endAnalysed = '?'
        if len(end) == 2:
            endAnalysed = parse_robinson_conjugation(end)
        elif len(end) == 3:
            endAnalysed = parse_robinson_declination([end], "verbe")
        return "verbe ({}, {})".format(tvmAnalysed, endAnalysed)

    return "verbe ({})".format(tvmAnalysed)

def parse_robinson_conjugation(pn):
    return "{} du {}".format(
            person.get(pn[0], '?'),
            number.get(pn[1], '?')
            )

def parse_robinson_personal(subMorph):
    cn = subMorph[0]
    return "pronom personnel, {} {}".format(
        case.get(cn[0], '?'),
        number.get(cn[1], '?'),
        )

def parse_robinson_declination(subMorph, wordType):
    
    cng = subMorph[0]
    cngAnalysed = "{} {} {}".format(
        case.get(cng[0], '?'),
        gender.get(cng[2], '?'),
        number.get(cng[1], '?')
        )

    if wordType == "verbe":
        return cngAnalysed
    else:
        return "{}, {}".format(
            wordType,
            cngAnalysed
        )

wordClasses = {
    'A': lambda x: parse_robinson_declination(x, "adjectif"),
    'ADV': lambda x: "adverbe",
    'C': lambda x: "pronom réciproque",
    'CONJ': lambda x: "conjonction",
    'D': lambda x: "pronom démonstratif",
    'F': lambda x: "pronom réfléchit",
    'I': lambda x: "pronom interrogatif",
    'K': lambda x: "pronom corrélatif",
    'N': lambda x: parse_robinson_declination(x, "nom"),
    'P': parse_robinson_personal,
    'PREP': lambda x: "préposition",
    'PRT': lambda x: "particule",
    'Q': lambda x: "pronom corrélatif ou interrogatif",
    'R': lambda x: parse_robinson_declination(x, "pronom relatif"),
    'S': lambda x: "pronom possessif",
    'T': lambda x: parse_robinson_declination(x, "article défini"),
    'V': parse_robinson_verb,
    'X': lambda x: "pronom indéfini",
}
