# Message Types
#-------------------------------------------------------------------------------------------------
MSGTYPE_NULL   = 0x00
MSGTYPE_GET    = 0x01
MSGTYPE_SET    = 0x02
MSGTYPE_REPORT = 0x03


# Attribute Types
#-------------------------------------------------------------------------------------------------
ATTRIB_TYPE_UNKNOWN	= 0x00	# Unknown type
ATTRIB_TYPE_INT8	= 0x01	# Two's complement integer, 8 bit
ATTRIB_TYPE_INT16	= 0x02	# Two's complement integer, 16 bit
ATTRIB_TYPE_INT32	= 0x03	# Two's complement integer, 32 bit
ATTRIB_TYPE_INT64	= 0x04	# Two's complement integer, 64 bit
ATTRIB_TYPE_UINT8	= 0x05	# Unsigned integer, 8 bit
ATTRIB_TYPE_UINT16	= 0x06	# Unsigned integer, 16 bit
ATTRIB_TYPE_UINT32	= 0x07	# Unsigned integer, 32 bit
ATTRIB_TYPE_UINT64	= 0x08	# Unsigned integer, 64 bit
ATTRIB_TYPE_BOOLEAN	= 0x09	# Boolean value in bit 0
ATTRIB_TYPE_STRING	= 0x0A	# ASCIIZ string
ATTRIB_TYPE_MAX		= ATTRIB_TYPE_STRING


# Attributes
#-------------------------------------------------------------------------------------------------
ATTRIB_NULL			= 0x0000	# NULL attribute
ATTRIB_ATTRIBUTE_COUNT		= 0x0001	# Attribute count - the number of attributes

# Attributes per Attribute Instance (attributes of attributes)
ATTRIB_ENUM			= 0x0002	# Attribute enum - uint16, one of these ATTRIB_xxx values
ATTRIB_NAME			= 0x0003	# Attribute name - ASCIIZ string ("Manufacturer", "Model Number", etc.)
ATTRIB_WRITABLE			= 0x0004	# Attribute writable - boolean, 0=Read Only, 1=Writable
ATTRIB_NONVOLATILE		= 0x0005	# Attribute non-volatile - boolean, 0=Volatile, 1=Nonvolatile
ATTRIB_TYPE			= 0x0006	# Attribute value type - uint8, one of the ATTRIB_TYPE_xxx values
ATTRIB_VALUE_LIST		= 0x0007	# Attribute possible values

# Attributes at the EndDevice level
ATTRIB_MANUFACTURER		= 0x0010	# Manufacturer name - ASCIIZ string
ATTRIB_MODEL			= 0x0011	# Model - ASCIIZ string
ATTRIB_SERIAL_NUMBER		= 0x0012	# Serial number - ASCIIZ string
ATTRIB_EXTENDED_ADDRESS		= 0x0013	# Globally unique address - UINT64 (802.15.4 extended address)
ATTRIB_FW_VERSION		= 0x0014	# FW version - ASCIIZ string
ATTRIB_HW_VERSION		= 0x0015	# HW version - ASCIIZ string
ATTRIB_PARENT_NODE		= 0x0016	# NW Parent - UINT16
ATTRIB_NEIGHBOR_COUNT		= 0x0017	# NW Neighbor Count - UINT8
ATTRIB_NEIGHBOR_NODE		= 0x0018	# NW Neighbors (multiple instances) - UINT16
ATTRIB_RX_SIGNAL_STRENGTH	= 0x0019	# Rx Signal strength (RSSI) - UINT8
ATTRIB_TX_POWER			= 0x001A	# Tx Signal power - UINT8
ATTRIB_CHANNEL_PAGE		= 0x001B	# Radio channel page - UINT8
ATTRIB_CHANNEL_MASK		= 0x001C	# Radio channel mask - UINT16
ATTRIB_NETWORK_PANID		= 0x001D	# PanId of network - UINT16
ATTRIB_LOG_ENTRY_COUNT		= 0x001E	# Log entry count - UINT8
ATTRIB_LOG_ENTRY_TEXT		= 0x001F	# Log entry text (multiple instances) - ASCIIZ string
ATTRIB_SENSOR_COUNT		= 0x0020	# Sensor count - UINT8
ATTRIB_NICKNAME			= 0x0021	# Nickname - ASCIIZ string
ATTRIB_SENSOR_ATTRIB_COUNT = 0x0022

# Attributes per Sensor (multiple instances of each)
ATTRIB_SENSOR_PROPERTY		= 0x0101	# Physical property measured - ASCIIZ string ("Temperature", "Voltage")
ATTRIB_SENSOR_UNITS		= 0x0102	# Units - ASCIIZ string ("Degrees C", "V")
ATTRIB_SENSOR_DATA_TYPE		= 0x0103	# Data type/size of reports (one of ATTRIB_TYPE_??? values)
ATTRIB_SENSOR_MINIMUM		= 0x0104	# Physical property min - example: -40 for lowest temperature measured
ATTRIB_SENSOR_MAXIMUM		= 0x0105	# Physical property max - example: 212 for highest temperature measured
ATTRIB_SENSOR_VALUE		= 0x0106	# Current value read by sensor - size/type controlled by ATTRIB_SENSOR_DATA_TYPE
ATTRIB_SENSOR_INTERVAL_ENABLE	= 0x0107	# Enable sending reports at a contant interval - Boolean
ATTRIB_SENSOR_INTERVAL_TIME	= 0x0108	# Interval report time of sensor - UINT16 (units depend on ATTRIB_SENSOR_INTERVAL_UNITS)
ATTRIB_SENSOR_INTERVAL_UNITS	= 0x0109	# Units for interval reporting (ms/sec/min/hour/day/week/month/year)
ATTRIB_SENSOR_THRESH_MIN_ENABLE	= 0x010A	# Enable sending reports if below minimum value - Boolean
ATTRIB_SENSOR_THRESH_MIN	= 0x010B	# Trigger minimum value, send report at or below this value
ATTRIB_SENSOR_THRESH_MAX_ENABLE	= 0x010C	# Enable sending reports if above maximum value - Boolean
ATTRIB_SENSOR_THRESHOLD_MAX	= 0x010D	# Trigger maximum value, send report at or above this value
ATTRIB_SENSOR_CHANGE_ENABLE	= 0x010E	# Enable sending reports only if value changes by a given % - Boolean
ATTRIB_SENSOR_CHANGE_PERCENT	= 0x010F	# Percent change that triggers sending a report
ATTRIB_SENSOR_ENABLE            = 0x0110

class AttribTypeEntry(object):
    def __init__(self, Attribute, Type, Name, ShortName):
        self.Attribute = Attribute
        self.Type = Type
        self.Name = Name
        self.ShortName = ShortName

AttribTypeTable = []
#                                       Attribute                       Data Type              Attribute Name          Short Name
#                                    -------------------------------   --------------------   ---------------------   -------------------
AttribTypeTable.append(AttribTypeEntry( ATTRIB_ATTRIBUTE_COUNT,         ATTRIB_TYPE_UINT16,    "Attribute Count",      "acnt"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_ENUM,                    ATTRIB_TYPE_UINT16,    "Enum",                 "enum"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_NAME,                    ATTRIB_TYPE_STRING,    "Name",                 "name"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_WRITABLE,                ATTRIB_TYPE_BOOLEAN,   "Writable",             "wrt"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_NONVOLATILE,             ATTRIB_TYPE_BOOLEAN,   "Nonvolatile",          "nv"    ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_TYPE,                    ATTRIB_TYPE_UINT8,     "Type",                 "type"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_VALUE_LIST,              ATTRIB_TYPE_STRING,    "Value List",           "vlst"  ))

# Attributes at the EndDevice level
AttribTypeTable.append(AttribTypeEntry( ATTRIB_MANUFACTURER,            ATTRIB_TYPE_STRING,    "Manufacturer",         "mfr"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_MODEL,                   ATTRIB_TYPE_STRING,    "Model",                "mod"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SERIAL_NUMBER,           ATTRIB_TYPE_STRING,    "Serial Number",        "ser"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_NICKNAME,                ATTRIB_TYPE_STRING,    "Nickname",             "nn"    ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_EXTENDED_ADDRESS,        ATTRIB_TYPE_UINT64,    "Extended Address",     "xadd"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_FW_VERSION,              ATTRIB_TYPE_STRING,    "Firmware Version",     "fwv"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_HW_VERSION,              ATTRIB_TYPE_STRING,    "Hardware Version",     "hwv"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_PARENT_NODE,             ATTRIB_TYPE_UINT16,    "Parent Node",          "par"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_NEIGHBOR_COUNT,          ATTRIB_TYPE_UINT8,     "Neighbor Count",       "ncnt"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_NEIGHBOR_NODE,           ATTRIB_TYPE_UINT16,    "Neighbor Node",        "nnod"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_RX_SIGNAL_STRENGTH,      ATTRIB_TYPE_UINT8,     "Rx Signal Strength",   "rx"    ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_TX_POWER,                ATTRIB_TYPE_UINT8,     "Tx Power",             "tx"    ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_CHANNEL_PAGE,            ATTRIB_TYPE_UINT8,     "Channel Page",         "cpg"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_CHANNEL_MASK,            ATTRIB_TYPE_UINT32,    "Channel Mask",         "cmk"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_NETWORK_PANID,           ATTRIB_TYPE_UINT16,    "PAN ID",               "pan"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_LOG_ENTRY_COUNT,         ATTRIB_TYPE_UINT8,     "Log Entry Count",      "lcnt"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_LOG_ENTRY_TEXT,          ATTRIB_TYPE_STRING,    "Log Entry Text",       "ltxt"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_COUNT,            ATTRIB_TYPE_UINT8,     "Sensor Count",         "scnt"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_ATTRIB_COUNT,     ATTRIB_TYPE_UINT16,     "Sensor Attribute Count","sacn"  ))

# Attributes per Sensor (multiple instances of each)
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_PROPERTY,         ATTRIB_TYPE_STRING,    "Property",             "prop"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_UNITS,            ATTRIB_TYPE_STRING,    "Units",                "unit"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_DATA_TYPE,        ATTRIB_TYPE_UINT8,     "Data Type",            "dtyp"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_MINIMUM,          ATTRIB_TYPE_STRING,   "Minimum",              "min"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_MAXIMUM,          ATTRIB_TYPE_STRING,   "Maximum",              "max"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_VALUE,           ATTRIB_TYPE_STRING,   "Value",                "val"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_VALUE,            ATTRIB_TYPE_UINT16,   "Value",                "val"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_INTERVAL_ENABLE,  ATTRIB_TYPE_BOOLEAN,   "Interval Enable",      "ien"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_INTERVAL_TIME,    ATTRIB_TYPE_UINT16,    "Interval Time",        "itm"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_INTERVAL_UNITS,   ATTRIB_TYPE_UINT8,     "Interval Units",       "iun"   ))# Units for interval reporting (ms/sec/min/hour/day/week/month/year)
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_THRESH_MIN_ENABLE,ATTRIB_TYPE_BOOLEAN,   "Threshold Min Enable", "tmne"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_THRESH_MIN,       ATTRIB_TYPE_STRING,   "Threshold Min Value",  "tmnv"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_THRESH_MAX_ENABLE,ATTRIB_TYPE_BOOLEAN,   "Threshold Max Enable", "tmxe"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_THRESHOLD_MAX,    ATTRIB_TYPE_STRING,   "Threshold Max Value",  "tmxv"  ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_CHANGE_ENABLE,    ATTRIB_TYPE_BOOLEAN,   "Change Enable",        "che"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_CHANGE_PERCENT,   ATTRIB_TYPE_UINT8,     "Change Percent",       "chp"   ))
AttribTypeTable.append(AttribTypeEntry( ATTRIB_SENSOR_ENABLE,           ATTRIB_TYPE_UINT8,     "Sensor Enable",        "se"   ))

def GetAttrType (Attrib):
    for x in AttribTypeTable:
        if x.Attribute == Attrib:
            return x.Type
    print 'UNKNOWN!!!!!!! ',Attrib
    return ATTRIB_TYPE_UNKNOWN

def EvalPacket(pkt):
    if pkt == None:
        print "Packet empty"
        return "Error"

    if len(pkt) < 13:
        #print "Packet too short"
        #print pkt
        return "Error"

    endpoint = pkt[0]
    if not endpoint == 1:
        print "Unknown endpoint in response"
        return "Error"

    sernum = ''.join([chr(x) for x in pkt[1:11]])
    lqi = pkt[11]
    rssi = pkt[12]

    #print endpoint, sernum, lqi, rssi

    msgBuf = pkt[13:]
    if len(msgBuf) < 5:
        print "Message too short"
        return "Error"

    if msgBuf[0] != 3: #MSGTYPE_REPORT
        print "Unknown message type"
        return "Error"

    msg = msgBuf[0:5]
    msgType = msg[0]
    attribute = (msg[1] << 8) + msg[2]
    instance = msg[3]
    payloadSize = msg[4]
    msgPayload = msgBuf[5:5+payloadSize]

    AttribType = GetAttrType(attribute)
    if AttribType == ATTRIB_TYPE_UNKNOWN:
        return "Unknown Attribute"
    if AttribType == ATTRIB_TYPE_UINT8:
        result = msgPayload[0]
    elif AttribType == ATTRIB_TYPE_STRING:
        result = ''
        for i in msgPayload:
            if not i==0:
                result+=chr(i)
    elif AttribType == ATTRIB_TYPE_BOOLEAN:
        result = (msgPayload[0] & 0x01) != 0
    elif AttribType == ATTRIB_TYPE_UINT16:
        result = msgPayload[0] + (msgPayload[1] << 8)
    elif AttribType == ATTRIB_TYPE_UINT32:
        result = msgPayload[0] + (msgPayload[1] << 8) + (msgPayload[2] << 16) + (msgPayload[3] << 24)
    elif AttribType == ATTRIB_TYPE_UINT64:
        result = msgPayload[0] + (msgPayload[1] << 8) + (msgPayload[2] << 16) + (msgPayload[3] << 24) + (msgPayload[4] << 32) + (msgPayload[5] << 40) + (msgPayload[6] << 48) + (msgPayload[7] << 56)
    else:
        result = "Unknown Type";
    return result
