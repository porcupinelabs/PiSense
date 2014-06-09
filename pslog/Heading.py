
def postprocess(params, readings):
    try:
        declination = int(params[0])
        heading=int(readings[0])
        heading += declination
        heading %= 360
    except :
        heading = (-1)
    return str(heading)
