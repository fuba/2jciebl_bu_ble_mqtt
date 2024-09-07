import bluetooth._bluetooth as bluez
import struct
import sys
import subprocess
import logging
import argparse
import paho.mqtt.client as mqtt
import os
import threading
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('2jcie_ble_mqtt')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Bluetooth adaptor
BT_DEV_ID = 0

# MQTT connection details
MQTT_HOST = os.getenv('MQTT_SERVER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USERNAME')
MQTT_PASS = os.getenv('MQTT_PASSWORD')
MQTT_BASE_TOPIC = os.getenv('MQTT_TOPIC', 'homeassistant/2jciebl-bu-ble')

# BLE OpCode group field for the LE related OpCodes.
OGF_LE_CTL = 0x08
# BLE OpCode Commands.
OCF_BLE_SET_SCAN_PARAMETERS = 0x000B
OCF_BLE_SET_SCAN_ENABLE = 0x000C

def reset_hci():
    try:
        # resetting bluetooth dongle
        cmd = "sudo hciconfig hci0 down"
        subprocess.call(cmd, shell=True)
        cmd = "sudo hciconfig hci0 up"
        subprocess.call(cmd, shell=True)
        logger.info("Bluetooth device reset successfully")
    except Exception as e:
        logger.error(f"Failed to reset Bluetooth device: {str(e)}")
        sys.exit(1)

def hci_le_set_scan_parameters(sock):
    cmd_pkt = struct.pack("<BBBBBBB", 0x01, 0x0, 0x10, 0x0, 0x10, 0x01, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_BLE_SET_SCAN_PARAMETERS, cmd_pkt)

def hci_le_enable_scan(sock):
    cmd_pkt = struct.pack("<BB", 0x01, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_BLE_SET_SCAN_ENABLE, cmd_pkt)

def hci_le_disable_scan(sock):
    cmd_pkt = struct.pack("<BB", 0x00, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_BLE_SET_SCAN_ENABLE, cmd_pkt)

def mqtt_connect(mqtt_host, mqtt_port, mqtt_user, mqtt_pass):
    client = mqtt.Client()
    if mqtt_user and mqtt_pass:
        client.username_pw_set(mqtt_user, mqtt_pass)
    client.connect(mqtt_host, mqtt_port, 60)
    return client

# Function to publish data to MQTT with modified topic
def publish_mqtt(client, base_topic, address, payload):
    modified_address = address.replace(":", "_")
    topic = f"{base_topic}/{modified_address}"
    client.publish(topic, payload)

def print_bu(packet, client, base_topic, address):
    company_id = str(format(packet[19],'x')+format(packet[20],'x').zfill(2))
    temperature = str(int(hex(packet[24])+format(packet[23],'x'), 16)/100)
    relative_humidity = str(int(hex(packet[26])+format(packet[25],'x'),16)/100)
    ambient_light = str(int(hex(packet[28])+format(packet[27],'x'),16))
    barometric_pressure = str(int(hex(packet[32])+format(packet[31],'x')+format(packet[30],'x')+format(packet[29],'x'),16)/1000)
    sound_noise = str(int(hex(packet[34])+format(packet[33],'x'),16)/100)
    etvoc = str(int(hex(packet[36])+format(packet[35],'x'),16))
    eco2 = str(int(hex(packet[38])+format(packet[37],'x'),16))
    
    data = {
        "time": int(time.time()),
        "company_id": company_id,
        "temperature": temperature,
        "relative_humidity": relative_humidity,
        "ambient_light": ambient_light,
        "barometric_pressure": barometric_pressure,
        "sound_noise": sound_noise,
        "etvoc": etvoc,
        "eco2": eco2
    }
    
    payload = json.dumps(data)
    publish_mqtt(client, base_topic, address, payload)
    
    logger.info(f"Published 2JCIE-BU data to MQTT topic {base_topic}/{address.replace(':', '_')}: " + payload)

def print_bl(packet, client, base_topic, address):
    company_id = format(packet[19], 'x') + format(packet[20], 'x').zfill(2)
    sequence_number = int(hex(packet[21]), 16)
    temperature = int(hex(packet[23]) + format(packet[22], 'x'), 16) / 100
    relative_humidity = int(hex(packet[25]) + format(packet[24], 'x'), 16) / 100
    ambient_light = int(hex(packet[27]) + format(packet[26], 'x'), 16)
    uv_index = int(hex(packet[29]) + format(packet[28], 'x'), 16) / 100
    pressure = int(hex(packet[31]) + format(packet[30], 'x'), 16) / 10
    sound_noise = int(hex(packet[33]) + format(packet[32], 'x'), 16) / 100
    discomfort_index = int(hex(packet[35]) + format(packet[34], 'x'), 16) / 100
    heat_stroke = int(hex(packet[37]) + format(packet[36], 'x'), 16) / 100
    battery_voltage = int(hex(packet[40]), 16)

    data = {
        "time": int(time.time()),
        "company_id": company_id,
        "sequence_number": sequence_number,
        "temperature": temperature,
        "relative_humidity": relative_humidity,
        "ambient_light": ambient_light,
        "uv_index": uv_index,
        "pressure": pressure,
        "sound_noise": sound_noise,
        "discomfort_index": discomfort_index,
        "heat_stroke": heat_stroke,
        "battery_voltage": battery_voltage
    }

    payload = json.dumps(data)
    publish_mqtt(client, base_topic, address, payload)
    
    logger.info(f"Published 2JCIE-BL data to MQTT topic {base_topic}/{address.replace(':', '_')}: {payload}")

def parse_events(sock, address, client, base_topic):
    old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)
    flt = bluez.hci_filter_new()
    bluez.hci_filter_all_events(flt)
    bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
    sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)

    while True:
        pkt = sock.recv(255)
        parsed_packet = hci_le_parse_response_packet(pkt)
        packet_bin = parsed_packet["packet_bin"]
        addr = ':'.join('%02x' % b for b in packet_bin[7:13][::-1])

        if addr.lower() == address.lower():
            logger.info(f"Received packet from {address}")
            if b'\xd5\x02' in packet_bin:
                if b'EP' in packet_bin:
                    print_bl(packet_bin, client, base_topic, addr)
                if b'Rbt' in packet_bin:
                    print_bu(packet_bin, client, base_topic, addr)

def hci_le_parse_response_packet(pkt):
    result = {}
    ptype, event, plen = struct.unpack("<BBB", pkt[:3])
    result["packet_type"] = ptype
    result["bluetooth_event_id"] = event
    result["packet_length"] = plen
    result["packet_str"] = pkt.hex()
    result["packet_bin"] = pkt
    return result

def process_ble_device(address, mqtt_host, mqtt_port, mqtt_user, mqtt_pass, base_topic):
    try:
        # Reset the Bluetooth device to ensure it's ready
        reset_hci()

        # Open Bluetooth device
        sock = bluez.hci_open_dev(BT_DEV_ID)

        # Set BLE scan parameters and enable scan
        hci_le_set_scan_parameters(sock)
        hci_le_enable_scan(sock)

        client = mqtt_connect(mqtt_host, mqtt_port, mqtt_user, mqtt_pass)
        logger.info(f"Listening for device {address}")

        parse_events(sock, address, client, base_topic)

    except Exception as e:
        logger.error(f"Exception for device {address}: {str(e)}")

    finally:
        hci_le_disable_scan(sock)

def main():
    parser = argparse.ArgumentParser(description='Connect to multiple BLE devices and send data to MQTT.')
    parser.add_argument('-a', '--addresses', required=True, help='Comma-separated BLE device addresses to connect to.')
    parser.add_argument('-H', '--mqtt_host', default=MQTT_HOST, help='MQTT broker host')
    parser.add_argument('-p', '--mqtt_port', default=MQTT_PORT, type=int, help='MQTT broker port')
    parser.add_argument('-u', '--mqtt_user', default=MQTT_USER, help='MQTT username')
    parser.add_argument('-P', '--mqtt_pass', default=MQTT_PASS, help='MQTT password')
    parser.add_argument('-t', '--mqtt_topic', default=MQTT_BASE_TOPIC, help='Base MQTT topic')
    args = parser.parse_args()

    addresses = [addr.strip() for addr in args.addresses.split(',')]
    mqtt_host = args.mqtt_host
    mqtt_port = args.mqtt_port
    mqtt_user = args.mqtt_user
    mqtt_pass = args.mqtt_pass
    mqtt_base_topic = args.mqtt_topic

    # Create a thread for each BLE device
    threads = []
    for address in addresses:
        thread = threading.Thread(target=process_ble_device, args=(address, mqtt_host, mqtt_port, mqtt_user, mqtt_pass, mqtt_base_topic))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
