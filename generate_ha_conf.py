import argparse

def generate_sensor_config(addresses):
    config = []
    for address in addresses:
        modified_address = address.lower().replace(":", "_")
        sensor_config = f"""
sensor:
  - name: "Temperature {address}"
    unique_id: "ble_sensor_temperature_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "°C"
    value_template: "{{{{ value_json.temperature }}}}"
    state_class: measurement
    device_class: temperature

  - name: "Humidity {address}"
    unique_id: "ble_sensor_humidity_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "%"
    value_template: "{{{{ value_json.relative_humidity }}}}"
    state_class: measurement
    device_class: humidity

  - name: "Ambient Light {address}"
    unique_id: "ble_sensor_ambient_light_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "lx"
    value_template: "{{{{ value_json.ambient_light }}}}"
    state_class: measurement
    device_class: illuminance

  - name: "UV Index {address}"
    unique_id: "ble_sensor_uv_index_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "UV Index"
    value_template: "{{{{ value_json.uv_index }}}}"
    state_class: measurement

  - name: "Barometric Pressure {address}"
    unique_id: "ble_sensor_barometric_pressure_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "hPa"
    value_template: "{{{{ value_json.pressure }}}}"
    state_class: measurement
    device_class: pressure

  - name: "Sound Noise {address}"
    unique_id: "ble_sensor_sound_noise_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "dB"
    value_template: "{{{{ value_json.sound_noise }}}}"
    state_class: measurement

  - name: "Discomfort Index {address}"
    unique_id: "ble_sensor_discomfort_index_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "DI"
    value_template: "{{{{ value_json.discomfort_index }}}}"
    state_class: measurement

  - name: "Heat Stroke {address}"
    unique_id: "ble_sensor_heat_stroke_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "°C"
    value_template: "{{{{ value_json.heat_stroke }}}}"
    state_class: measurement

  - name: "Battery Voltage {address}"
    unique_id: "ble_sensor_battery_voltage_{modified_address}"
    state_topic: "homeassistant/2jciebl-bu-ble/{modified_address}"
    unit_of_measurement: "mV"
    value_template: "{{{{ value_json.battery_voltage }}}}"
    state_class: measurement
    device_class: battery
        """
        config.append(sensor_config)
    return config

def main():
    parser = argparse.ArgumentParser(description="Generate Home Assistant sensor config for BLE devices.")
    parser.add_argument("-a", "--addresses", required=True, help="Comma-separated list of BLE device addresses.")
    args = parser.parse_args()

    # Split and clean the addresses
    addresses = [addr.strip() for addr in args.addresses.split(",")]

    # Generate the configuration
    config = generate_sensor_config(addresses)

    # Output the configuration
    for entry in config:
        print(entry)

if __name__ == "__main__":
    main()
