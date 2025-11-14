from machine import Pin, ADC, reset
import time
import utime
import ubinascii
import network
import json
import io
from lib.mqttclient import MQTTClient

probe_analog = ADC(Pin(26))  # ADC0 on Pyboard
led = Pin("LED", Pin.OUT)

MEASUREMENT_INTERVAL = 30  # seconds

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
            self.client.publish(topic, moistureOutput.to_json())
        except Exception as e:
            print("Failed to publish moisture:", e)
            raise e

class Moisture:
    def __init__(self, measure):
        self.measure = measure
        self.ts = utime.time()

    def to_json(self):
        return json.dumps(self.__dict__)
    
def restart_and_reconnect():
  print('Restart and Reconnect...')
  time.sleep(10)
  reset()

def main():
    led.off()

    with open("setting.json", "r") as appsetting:
        settings = json.load(appsetting)
        WIFI_SSID = settings["WIFI_SSID"]
        WIFI_PASSWORD = settings["WIFI_PASSWORD"]
        MQTT_CLIENT_ID = ubinascii.hexlify(settings["MQTT_CLIENT_ID"])
        MQTT_BROKER = settings["MQTT_BROKER"]
        MQTT_MOISTURE_TOPIC = settings["MQTT_TOPIC"].encode('utf-8')
        MQTT_USERNAME = settings["MQTT_USERNAME"]
        MQTT_PASSWORD = settings["MQTT_PASSWORD"]

    wifi_manager = WifiManager(WIFI_SSID, WIFI_PASSWORD)
    mqtt_manager = MqttManager(
        MQTT_CLIENT_ID,
        MQTT_BROKER,
        MQTT_MOISTURE_TOPIC,
        MQTT_USERNAME,
        MQTT_PASSWORD
    )
    moisture_sensor = MoistureSensor(probe_analog)

    if not wifi_manager.wifi_connect():
        print("Could not connect to WiFi")
        return

    try:
        mqtt_manager.mqtt_connect()
    except Exception as e:
        print("Could not connect to MQTT Broker:", e)
        wifi_manager.wifi_disconnect()
        return

    try:
        while True:
            led.on()
            moisture = moisture_sensor.read_moisture()
            mqtt_manager.publish_moisture(MQTT_MOISTURE_TOPIC, moisture)
            print("Published moisture:", moisture)
            led.off()
            time.sleep(MEASUREMENT_INTERVAL)
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print("An error occurred:", e)
        restart_and_reconnect()
    finally:
        mqtt_manager.mqtt_disconnect()
        wifi_manager.wifi_disconnect()

if __name__ == "__main__":
    main()