

def postprocess(params, readings):
    initial=readings[0]
    calibrated=int(initial)+params[0]
    return str(calibrated)