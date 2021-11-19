from theke.morphology.oshm_morph import parse_oshm
from theke.morphology.robinson_morph import parse_robinson

def parse(morph):
    '''Parse a morphology string.

    @param morph: (string)
        Ex. oshm:HC_Ncbdc_Sp3ms
    '''
    morph = morph.split(':')

    if len(morph) > 1:
        if morph[0] == 'oshm':
            return parse_oshm(morph[1])
        elif morph[0].lower() == 'robinson':
            return parse_robinson(morph[1])
        elif morph[0].lower() == 'packard':
            return [morph[1]]
    else:
        return None