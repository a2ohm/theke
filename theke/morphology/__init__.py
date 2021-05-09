from theke.morphology.oshm_morph import parse_oshm

def parse(morph):
    '''Parse a morphology string.

    @param morph: (string)
        Ex. oshm:HC_Ncbdc_Sp3ms
    '''
    morph = morph.split(':')

    if len(morph) > 1 and morph[0] == 'oshm':
        return parse_oshm(morph[1])
    else:
        return None