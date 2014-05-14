import math

def postprocess(params, readings):
    try:
        scale=params[0];
        accx=float(readings[0])/scale *-1 #axis opposite on the devices
        accy=float(readings[1])/scale *-1
        accz=float(readings[2])/scale
        x=float(readings[3])
        y=float(readings[4])
        z=float(readings[5])
        roll=math.asin(accy)#in radians
        pitch=math.asin(accx)
        xc= x * math.cos(pitch) - z * math.sin(pitch)
        yc = x * math.sin(roll) * math.sin(pitch) + y * math.cos(roll) - z* math.sin(roll) * math.cos(pitch)
        tan = yc/xc
        heading = format( ( math.atan(tan) * 180 / 3.1415927) + 180, '.1f')
    except:
        heading=-1
        print scale,accx,accy,accz,x,y,z,roll,pitch,xc,yc
    return str(heading)