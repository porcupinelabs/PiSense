import time

def event_trigger(params, triggers, datetime):
    try:
        #detect motion
        accelList=triggers.split(',')
        #in each list is instantaneous, min, max, avg values
        if accelList[1]!= accelList[2]:
            try:
                f=open('events.csv','a')
                f.write(time.asctime(time.gmtime(datetime)) + ',' + 'motion\n')
                f.close()
            except:
                print ('cannot record to events log')
            f.close()
    except:
        pass



