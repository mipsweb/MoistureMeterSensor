# MoistureMeter Sensor

A MicroPython-based moisture sensor monitoring system that measures soil moisture levels and publishes data to an MQTT broker. Perfect for IoT applications like plant watering automation and garden monitoring.

## Features

- **Real-time Moisture Monitoring**: Reads analog moisture sensor data and converts to percentage values
- **WiFi Connectivity**: Connects to WiFi networks for internet communication
- **MQTT Integration**: Publishes moisture readings to an MQTT broker for remote monitoring
- **Configurable Settings**: JSON-based configuration for easy customization
- **Error Handling**: Robust MQTT error handling on the `mqtt_error_handling` branch
- **Periodic Measurements**: Configurable measurement intervals (default: 30 seconds)

## Hardware Requirements

- Raspberry Pi Pico or similar MicroPython-compatible board
- Soil moisture sensor (analog output)
- WiFi connectivity (built-in or module)
- LED (for status indication)

## Project Structure

```
MoistureMeter/
├── main.py              # Main application logic
├── setting.json         # Configuration file (WiFi, MQTT credentials)
└── lib/
    └── mqttclient.py    # MQTT client implementation
    └── ntptime.py       # NTP time implementation
```

## Configuration

Edit `setting.json` to configure your WiFi and MQTT settings:

```json
{
    "WIFI_SSID": "your_wifi_network",
    "WIFI_PASSWORD": "your_wifi_password",
    "MQTT_CLIENT_ID": "unique_client_id",
    "MQTT_BROKER": "your_mqtt_broker_ip",
    "MQTT_TOPIC": "topic/path/for/moisture",
    "MQTT_USERNAME": "mqtt_username",
    "MQTT_PASSWORD": "mqtt_password",
    "MEASUREMENT_INTERVAL": 60,
    "NTP_SERVER": "pool.ntp.org"
}
```

## Dependencies

- MicroPython standard library modules:
  - `machine` - Hardware control (ADC, GPIO)
  - `network` - WiFi connectivity
  - `asyncio` - Asynchronous operations
  - `json` - Configuration parsing

## Usage

1. **Update Configuration**: Modify `setting.json` with your WiFi and MQTT broker details
2. **Upload Files**: Transfer `main.py`, `setting.json`, and `lib/mqttclient.py` to your Pico
3. **Run**: Execute `main.py` on the MicroPython device

The sensor will:
- Connect to WiFi
- Read moisture levels at regular intervals
- Publish readings to the configured MQTT topic

## Components Overview

### MoistureSensor Class
Handles analog reading from the moisture sensor and converts raw ADC values (0-65535) to moisture percentage (0-100%).

### WifiManager Class
Manages WiFi connection, handling SSID/password authentication and connection status monitoring.

### MQTTClient Class
Implements the MQTT protocol for publishing sensor data to a remote broker, including support for authentication and error handling.

## Development

**Current Branch**: `mqtt_error_handling` - Active development on MQTT error handling improvements

## License
No License

## Author

mipsweb
