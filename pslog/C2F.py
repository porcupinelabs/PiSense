

def postprocess(params, readings):
    degC=readings[0]
    degF=format(float(degC)*9/5+32,'.1f')
    #params unused
    return str(degF)