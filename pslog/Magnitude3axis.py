import math

def postprocess(params, readings):
    scale=params[0]
    x=float(readings[0])/scale
    y=float(readings[1])/scale
    z=float(readings[2])/scale
    mag=x*x+y*y+z*z
    mag=format(math.sqrt(mag),'.4f')
    return str(mag)