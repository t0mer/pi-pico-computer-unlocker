import os
import ssl
import time
import json
import wifi
import usb_hid
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keyboard_layout_win_uk import KeyboardLayout as KeyboardLayoutUK
from adafruit_hid.keyboard_layout_win_tr import KeyboardLayout as KeyboardLayoutTR
from adafruit_hid.keyboard_layout_win_sw import KeyboardLayout as KeyboardLayoutSW
from adafruit_hid.keyboard_layout_win_po import KeyboardLayout as KeyboardLayoutPO
from adafruit_hid.keyboard_layout_win_it import KeyboardLayout as KeyboardLayoutIT
from adafruit_hid.keyboard_layout_win_hu import KeyboardLayout as KeyboardLayoutHU
from adafruit_hid.keyboard_layout_win_fr import KeyboardLayout as KeyboardLayoutFR
from adafruit_hid.keyboard_layout_win_es import KeyboardLayout as KeyboardLayoutES
from adafruit_hid.keyboard_layout_win_de import KeyboardLayout as KeyboardLayoutDE
from adafruit_hid.keyboard_layout_win_da import KeyboardLayout as KeyboardLayoutDA
from adafruit_hid.keyboard_layout_win_cz import KeyboardLayout as KeyboardLayoutCZ
from adafruit_hid.keyboard_layout_win_br import KeyboardLayout as KeyboardLayoutBR


MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = os.getenv('MQTT_PORT')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_TOPIC = os.getenv('MQTT_TOPIC')
TOKEN = os.getenv('TOKEN')
HID_LAYOUT = os.getenv('HID_LAYOUT')
kbd = Keyboard(usb_hid.devices)

def get_keyboard_layout(kbd):
    #Get the desired layout from the Environment variables
    HID_LAYOUT = os.getenv('HID_LAYOUT')

    # Dictionary to map the HID_LAYOUT environment variable to the corresponding keyboard layout class
    layout_map = {
        'US': KeyboardLayoutUS,
        'UK': KeyboardLayoutUK,
        'TR': KeyboardLayoutTR,
        'SW': KeyboardLayoutSW,
        'PO': KeyboardLayoutPO,
        'IT': KeyboardLayoutIT,
        'HU': KeyboardLayoutHU,
        'FR': KeyboardLayoutFR,
        'ES': KeyboardLayoutES,
        'DE': KeyboardLayoutDE,
        'DA': KeyboardLayoutDA,
        'CZ': KeyboardLayoutCZ,
        'BR': KeyboardLayoutBR
    }
    # Get the layout class based on the environment variable
    LayoutClass = layout_map.get(HID_LAYOUT)

    # If no layout is found (invalid HID_LAYOUT value), you could default to US layout or raise an error
    if LayoutClass is None:
        raise ValueError("Unsupported or undefined keyboard layout")

    # Create an instance of the layout class
    return LayoutClass(kbd)

def wifi_connected():
    """Check if the device is connected to WiFi."""
    return wifi.radio.ipv4_address is not None

print("Connecting to WiFi")
# while not wifi_connected():
#     print(".")
#     #  connect to your SSID
wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
device_ip = wifi.radio.ipv4_address
print("Connected to WiFi")
print(f"My IP address is {str(device_ip)}")

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

mqtt_client = MQTT.MQTT(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    username=MQTT_USERNAME,
    password=MQTT_PASSWORD,
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
    socket_timeout=1 
)

# Define callback methods which are called when events occur
def connected(client, userdata, flags, rc):
    # This function will be called when the client connects to the broker
    print("Connected to MQTT Broker!")
    client.subscribe(MQTT_TOPIC)

def disconnected(client, userdata, rc):
    # This function will be called when the client disconnects from the broker
    print("Disconnected from MQTT Broker!")

def message(client, topic, message):
    # This function will be called when a message is received from the broker
    try:
        
        
        # Parse the message from JSON format to a Python dictionary
        data = json.loads(message)
        
        # Access token and password from the parsed JSON data
        received_token = data['token']
        received_password = data['password']
        
        # Validate the token
        if received_token == TOKEN:
            kbd.press(Keycode.SPACE)
            kbd.release_all()
            time.sleep(1)
            layout.write(received_password)
            time.sleep(1)
            kbd.press(Keycode.ENTER)
            kbd.release_all()
            time.sleep(1)
        else:
            print("Invalid token.")
    
    except KeyError:
        print("Missing data in message")
    except Exception as e:
        print(f"Error decoding JSON: {e}")

if __name__ == "__main__":
    layout = get_keyboard_layout(kbd)
    # Connect callbacks to client
    mqtt_client.on_connect = connected
    mqtt_client.on_disconnect = disconnected
    mqtt_client.on_message = message
    mqtt_client.keep_alive = 60

    # Connect to MQTT Broker
    mqtt_client.connect()
    
    try:
        mqtt_client.publish(f"{MQTT_TOPIC}/ip", str(device_ip))
        while True:
            mqtt_client.loop(timeout=1.5)
            time.sleep(1)
    except Exception as e:
        print("An error occurred in the MQTT loop:", str(e))
    except KeyboardInterrupt:
        pass

