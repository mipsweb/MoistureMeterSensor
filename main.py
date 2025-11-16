from machine import Pin, ADC, reset
import time
import utime
import ubinascii
import network
import json
from lib.mqttclient import MQTTClient
import asyncio
from lib.ntptime import settime

probe_analog = ADC(Pin(26))  # ADC0 on Pyboard
led = Pin("LED", Pin.OUT)

measure_pool = []

class MoistureSensor:
    def __init__(self, adc):
        self.adc = adc

    def read_moisture(self):
        # Read the analog value from the moisture sensor
        analog_value = self.adc.read_u16()
        # Convert to percentage (assuming 0 = wet, 65535 = dry)
        moisture_percentage = 100-((analog_value / 65535) * 100)
        return moisture_percentage
    
class WifiManager:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)

    def wifi_connect(self):
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        time.sleep(5)
        
        max_wait = 10
        while max_wait > 0:
            if self.wlan.status() < 0 or self.wlan.status() >= 3:
                break
            
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)
    
        if self.wlan.status() != 3:
            return False
        
        return True
    
    def wifi_disconnect(self):
        self.wlan.disconnect()
        self.wlan.active(False)

class MqttManager:
    def __init__(
        self,
        client_id,
        broker,
        topic, 
        user, 
        password
    ):
        self.client = MQTTClient(
            client_id,
            broker,
            1883,
            user,
            password,
            keepalive=60,
            ssl=False
        )
        self.topic = topic

    def mqtt_connect(self):
        try:
            self.client.connect()
        except Exception as e:
            print("MQTT connection failed:", e)
            raise e

    
    def mqtt_disconnect(self):
        try:
            self.client.disconnect()
        except Exception as e:
            print("MQTT disconnection failed:", e)
            raise e
    
    def publish_moisture(self, topic, moisture):
        try:
            moistureOutput = Moisture(moisture)
            self.client.publish(topic, moistureOutput.measure)
        except Exception as e:
            print("Failed to publish moisture:", e)
            raise e

class Moisture:
    def __init__(self, measure):
        self.measure = measure
        self.ts = utime.time()    

class MoistureHandler:
    def __init__(self, measure_pool):
        self.measure_pool = measure_pool        

    def add_measure(self, measure):
        self.measure_pool.append(measure)

        if(len(self.measure_pool) > 100):
            self.measure_pool.pop(0)       

    def get_last_measure(self) -> str | None:
        if len(self.measure_pool) > 0:
            x = self.measure_pool.pop()
            return json.dumps({"measure": x.measure, "ts": x.ts})
        else:
            return None
    
def restart_and_reconnect():
  print('Restart and Reconnect...')
  time.sleep(10)
  reset()


async def MqttWorker(wifi_manager, mqtt_manager, topic, ntp_server, moistureHandler, cancelToken=None):
    while True and (cancelToken is None or not cancelToken.is_set()):
        while True:
            try:
                if not wifi_manager.wlan.isconnected():
                    print("WiFi disconnected, attempting to reconnect...")
                    if not wifi_manager.wifi_connect():
                        print("Could not reconnect to WiFi, retrying in 10 seconds...")
                        await asyncio.sleep(10)
                        continue


                settime(ntp_server)

                mqtt_manager.mqtt_connect()
                print("Connected to MQTT Broker")
                break
            except Exception as e:
                print("Could not connect to MQTT Broker:", e)
                wifi_manager.wifi_disconnect()
                print("Retrying in 10 seconds...")
                await asyncio.sleep(10)
                
        while True:
            try:        
                last_measure = moistureHandler.get_last_measure()
                if last_measure is not None:
                    mqtt_manager.publish_moisture(topic, last_measure)
            
                await asyncio.sleep(1)
            except Exception as e:
                print("Error in MQTT Worker:", e)
                print("Reconnecting...")
                break


async def sensor_loop(interval, moisture_sensor, moisture_handler):
    try:
        moisture_sensor = MoistureSensor(probe_analog)

        while True:
            led.on()
            moisture_value = moisture_sensor.read_moisture()

            moisture = Moisture(moisture_value)

            moisture_handler.add_measure(moisture)
            led.off()
            await asyncio.sleep(interval)
    except Exception as e:
        print("An error occurred in sensor loop:", e)
        raise e

async def main():
    led.off()

    moisture_handler = MoistureHandler(measure_pool)

    with open("setting.json", "r") as appsetting:
        settings = json.load(appsetting)
        WIFI_SSID = settings["WIFI_SSID"]
        WIFI_PASSWORD = settings["WIFI_PASSWORD"]
        MQTT_CLIENT_ID = ubinascii.hexlify(settings["MQTT_CLIENT_ID"])
        MQTT_BROKER = settings["MQTT_BROKER"]
        MQTT_MOISTURE_TOPIC = settings["MQTT_TOPIC"].encode('utf-8')
        MQTT_USERNAME = settings["MQTT_USERNAME"]
        MQTT_PASSWORD = settings["MQTT_PASSWORD"]
        MEASUREMENT_INTERVAL = settings["MEASUREMENT_INTERVAL"]
        NTP_SERVER = settings["NTP_SERVER"]

    wifi_manager = WifiManager(WIFI_SSID, WIFI_PASSWORD)
    mqtt_manager = MqttManager(
        MQTT_CLIENT_ID,
        MQTT_BROKER,
        MQTT_MOISTURE_TOPIC,
        MQTT_USERNAME,
        MQTT_PASSWORD
    )

    sensor_task = asyncio.create_task(sensor_loop(MEASUREMENT_INTERVAL, MoistureSensor(probe_analog), moisture_handler))
    mqtt_task = asyncio.create_task(MqttWorker(wifi_manager, mqtt_manager, MQTT_MOISTURE_TOPIC, NTP_SERVER, moisture_handler))

    await asyncio.gather(sensor_task, mqtt_task)
    


if __name__ == "__main__":
    asyncio.run(main())