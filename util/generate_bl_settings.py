#!/usr/bin/env python3
"""Generate little-endian GATT values for low-power 2JCIE-BL settings."""

import argparse
import struct


def adv_setting(
    advertise_interval_ms,
    transmit_period,
    cycle,
    tx_power,
):
    if not 500 <= advertise_interval_ms <= 10240:
        raise ValueError("advertise interval must be between 500 and 10240 ms")
    if not 1 <= transmit_period <= 16383:
        raise ValueError("transmit period must be between 1 and 16383 seconds")
    silent_period = cycle - transmit_period
    if not 1 <= silent_period <= 16383:
        raise ValueError("cycle - transmit period must be between 1 and 16383 seconds")
    if tx_power not in (-20, -16, -12, -8, -4, 0, 4):
        raise ValueError("tx power must be one of -20, -16, -12, -8, -4, 0, 4 dBm")

    interval_units = round(advertise_interval_ms / 0.625)
    actual_interval_ms = interval_units * 0.625
    if abs(actual_interval_ms - advertise_interval_ms) > 1e-9:
        raise ValueError("advertise interval must be a multiple of 0.625 ms")

    # ADV_NONCON_IND interval is unused by the 2JCIE-BL. Keep its default.
    nonconnectable_interval_units = 0x00A0
    limited_broadcaster_2 = 0x05
    return struct.pack(
        "<HHHHBb",
        interval_units,
        nonconnectable_interval_units,
        transmit_period,
        silent_period,
        limited_broadcaster_2,
        tx_power,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate 2JCIE-BL Limited Broadcaster 2 GATT values."
    )
    parser.add_argument(
        "--measurement-interval",
        type=int,
        default=600,
        help="Measurement interval in seconds (1-3600; default: 600).",
    )
    parser.add_argument(
        "--cycle",
        type=int,
        default=600,
        help="Transmit + silent cycle in seconds (default: 600).",
    )
    parser.add_argument(
        "--transmit-period",
        type=int,
        default=10,
        help="Transmit window in seconds (default: 10).",
    )
    parser.add_argument(
        "--advertise-interval-ms",
        type=float,
        default=1285,
        help="ADV_IND interval in ms (default: 1285).",
    )
    parser.add_argument(
        "--tx-power",
        type=int,
        default=0,
        help="Tx power in dBm: -20, -16, -12, -8, -4, 0, or 4 (default: 0).",
    )
    args = parser.parse_args()

    if not 1 <= args.measurement_interval <= 3600:
        parser.error("measurement interval must be between 1 and 3600 seconds")

    try:
        adv_value = adv_setting(
            args.advertise_interval_ms,
            args.transmit_period,
            args.cycle,
            args.tx_power,
        )
    except ValueError as error:
        parser.error(str(error))

    measurement_value = struct.pack("<H", args.measurement_interval)
    print("Measurement interval (0x3011):", measurement_value.hex())
    print("ADV setting          (0x3042):", adv_value.hex())
    print("Power-cycle the sensor after writing 0x3042.")


if __name__ == "__main__":
    main()
