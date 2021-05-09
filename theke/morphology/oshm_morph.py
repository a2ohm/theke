def parse_oshm(morph):
    analysis = ''

    for subMorph in morph[1:].split('_'):
        wordClass = subMorph[0]

        if wordClass == 'A':
            analysis += "adjectif"

        elif wordClass == 'C':
            analysis += "conjonction ; "

        elif wordClass == 'D':
            analysis += "adverbe"

        elif wordClass == 'N':
            analysis += "nom"

        elif wordClass == 'P':
            analysis += "pronom démonstratif"

        elif wordClass == 'R':
            analysis += "préposition"

        elif wordClass == 'T':
            analysis += "particule"

        elif wordClass == 'V':
            analysis += "verbe"
            
        else:
            analysis += "inconnu"
    
    return analysis