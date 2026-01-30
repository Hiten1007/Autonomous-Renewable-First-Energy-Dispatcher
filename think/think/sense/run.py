import json
import ssl
import time
from datetime import datetime
from paho.mqtt import client as mqtt

ENDPOINT = "a1pibwes5rye3c-ats.iot.ap-south-1.amazonaws.com"
CLIENT_ID = "society_simulator"
TOPIC = "sense/telemetry"

client = mqtt.Client(
    client_id=CLIENT_ID,
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)


client.tls_set(
    ca_certs="certs/AmazonRootCA1.pem",
    certfile="certs/device.pem.crt",
    keyfile="certs/private.pem.key",
    tls_version=ssl.PROTOCOL_TLSv1_2
)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected with result code 0")
    else:
        print(f"Connection failed with reason code {reason_code}")


client.on_connect = on_connect

client.connect(ENDPOINT, 8883)
client.loop_start()

while True:
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "solar_kw": 10.2,
        "battery_soc": 0.45,
        "load_kw": 12.8,
        "grid_carbon_intensity": 650,
        "quality": {
            "solar": "fresh",
            "load": "fresh",
            "carbon": "fresh"
        }
    }

    client.publish(TOPIC, json.dumps(payload), qos=1)
    print("📡 Published:", payload)
    time.sleep(20)
