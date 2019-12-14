from influxdb import InfluxDBClient
import Adafruit_DHT
import requests
import time
import datetime
import math
import pprint
import os
import signal
import serial
import sys

bot_token = os.environ['BOT_TOKEN']
bot_chatID = os.environ['BOT_CHAT']
client = None
db_host = 'influxdb'
db_port = '8086'
dbname = 'mydb'
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
serialport='/dev/serial0'
CO2_MAX = 900
HUMIDITY_MIN = 30
# set yesterday as default date for the last alert 
co2_alert_sending_date = (datetime.datetime.now()- datetime.timedelta(days=1)).date()
humidity_alert_sending_date = (datetime.datetime.now()- datetime.timedelta(days=1)).date()

def telegram_bot_sendtext(bot_message):
    print('sending message to telegram:' + bot_message)
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)

def alert_if_needed(c, h):
    global co2_alert_sending_date
    global humidity_alert_sending_date
    today = datetime.datetime.today().date()
    if c > CO2_MAX and co2_alert_sending_date != today:
        telegram_bot_sendtext('CO2: %s' % (c))
        co2_alert_sending_date = today
    elif h < HUMIDITY_MIN and humidity_alert_sending_date != today:
        telegram_bot_sendtext('Humidity: %s' % (h))
        humidity_alert_sending_date = today

def db_exists():
    dbs = client.get_list_database()
    for db in dbs:
        if db['name'] == dbname:
            return True
    return False

def wait_for_server():
    # wait for the server to come online after starting docker container
    url = 'http://{}:{}'.format(db_host,db_port)
    waiting_time = 5
    for i in range(10):
        try:
            requests.get(url)
            return 
        except requests.exceptions.ConnectionError:
            print('waiting for', url)
            time.sleep(waiting_time)
            waiting_time *= 2
            pass
    print('cannot connect to', url)
    sys.exit(1)

def connect_db(db_host,db_port):
    #connect to the database, and create it if it does not exist
    global client
    print('connecting to database: {}:{}'.format(db_host,db_port))
    client = InfluxDBClient(db_host,db_port, retries=5, timeout=1)
    wait_for_server()
    if not db_exists():
        print('creating database...')
        client.create_database(dbname)
    else:
        print('database already exists')
    client.switch_database(dbname)

def get_humidity_and_temp():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

    if humidity is not None and temperature is not None:
        return [datetime.datetime.now(), humidity, temperature]
    else:
        sys.stderr.write("Error. Failed to retrieve data from humidity sensor")
        return False

#Function to calculate MH-Z19 crc according to datasheet
def crc8(a):
    crc=0x00
    count=1
    b=bytearray(a)
    while count<8:
        crc+=b[count]
        count=count+1
    #Truncate to 8 bit
    crc%=256
    #Invert number with xor
    crc=~crc&0xFF
    crc+=1
    return crc   

def get_co2(ser):
    #Send "read value" command to MH-Z19 sensor
    result=ser.write("\xff\x01\x86\x00\x00\x00\x00\x00\x79")
    time.sleep(0.1)
    s=ser.read(9)
    z=bytearray(s)
    crc=crc8(s)
    #Calculate crc
    if crc != z[8]:
        sys.stderr.write('CRC error calculated %d bytes= %d:%d:%d:%d:%d:%d:%d:%d crc= %dn' % (crc, z[0],z[1],z[2],z[3],z[4],z[5],z[6],z[7],z[8]))
    co2value=ord(s[2])*256 + ord(s[3])
    now=time.ctime()
    parsed=time.strptime(now)
    lgtime=time.strftime("%Y %m %d %H:%M:%S")
    return [datetime.datetime.now(),co2value]  

def measure(ser):
    ht_time, humidity, temperature = get_humidity_and_temp()
    co2_time, co2 = get_co2(ser)
    alert_if_needed(co2, humidity)
    data = [{
        'measurement':'humidity_and_temp',
        'time':ht_time,
        'fields' : {
            'humidity' : humidity,
            'temperature' : temperature,
        }},
        {
        'measurement':'co2',
        'time':co2_time,
        'fields' : {
            'val' : co2
        }}]
    pprint.pprint(data)
    try: 
        client.write_points(data)
    except Exception as e:
        sys.stderr.write("Error while writing to db:")
        sys.stderr.write(e)
        print("Trying one more time...")
        client.write_points(data)
    time.sleep(60)
    
if __name__ == '__main__':
    connect_db(db_host,db_port)
    try:
        # try to read a line of data from the serial port and parse    
        with serial.Serial(serialport, 9600, timeout=2.0) as ser:
            # loop will exit with Ctrl-C, which raises a KeyboardInterrupt
            while True:
                measure(ser)
    except Exception as e:
        sys.stderr.write('Error %s: %sn' % (type(e).__name__, e))
        ser.close()
        telegram_bot_sendtext('Error %s' % (type(e).__name__))
    except KeyboardInterrupt as e:
        ser.close()
        sys.stderr.write('nCtrl+C pressed, exiting log of %s to %sn' % (serialport, outfname))        
