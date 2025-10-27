# pytza500
[![License](https://img.shields.io/github/license/artifex-engineering/pytza500)](https://github.com/artifex-engineering/pytza500/blob/main/LICENSE)
![PyPI - Status](https://img.shields.io/pypi/status/pytza500)
![PyPI - Version](https://img.shields.io/pypi/v/pytza500)

**Python library for the Artifex Engineering TZA500**


## Installation
Install via pip:
```bash
pip install pytza500
```

Install manually:
```bash
git clone https://github.com/artifex-engineering/pytza500.git
cd pytza500
pip install .
```

## Usage
```python
from pytza500 import TZA500, GAIN, UNITS, BANDWITH

# List all available devices
devices = TZA500.find_devices() # Get all available devices
print("Available Devices: {}\n\n".format(", ".join(devices) if len(devices) > 0 else "None"))

# Create TZA500 instance
tza = TZA500()

# Connect to first TZA500 device in list
tza.connect(devices[0])

tza.tza_set_polarity(False) # Set polarity to not inverted

tza.tza_set_auto_zero() # Set initial auto zero

# Or set initial auto zero reset
tza.tza_set_auto_zero_reset()


tza.tza_set_bandwith(BANDWITH.KHZ_10) # Set bandwith to 100 kHz

# Set wavelength
tza.tza_set_wavelength(660)

# Set gain
tza.tza_set_gain(GAIN.X1)

tza.sensitivity = 1.0 # Set sensitivity (only for watt units)

# Set unit to use in measurements
tza.set_unit(UNITS.MICROAMPERE)

# Print single measurement
print(format(tza.tza_get_measurement(), '.8f'))

tza.disconnect()
```

## Query current states and device informations
```python
print("Firmware version: {}".format(tza.tza_firmware_version))
print("Serial number: {}".format(tza.tza_serial_number))
print("Date of manufacturing: {}".format(tza.tza_date_of_manufacturing))

print("Device info:\n{}\n\n".format(tza.tza_get_info()))

print("Polarity inverted: {}\n\n".format(tza.tza_is_polarity_inverted()))
print("Initial auto zero: {}".format(tza.initial_auto_zero))
print("Current sensitivity: {}\n\n".format(tza.sensitivity))
print("Current bandwith: {}".format(tza.tza_get_bandwith()))
print("Current wavelength: {}".format(tza.tza_get_wavelength()))
print("Current gain: {}".format(tza.tza_get_gain()))
print("Current Unit: {}".format(tza.unit))
```

## Available Units
- **Nanoampere (nA)**: UNITS.NANOAMPERE
- **Microampere (µA)**: UNITS.MICROAMPERE
- **Milliampere (mA)**: UNITS.MILLIAMPERE
- **Ampere (A)**: UNITS.AMPERE
- **Nanowatts (nW)**: UNITS.NANOWATTS
- **Microwatts (µW)**: UNITS.MICROWATTS
- **Milliwatts (mW)**: UNITS.MILLIWATTS
- **Watts (W)**: UNITS.WATTS

## Gain levels:
- **x1**: GAIN.X1
- **x10**: GAIN.X10
- **x100**: GAIN.X100
- **x1000**: GAIN.X1000
- **x10000**: GAIN.X10000
- **x100000**: GAIN.X100000
- **Auto**: GAIN.AUTO

## Bandwiths
- **10 kHz**: BANDWITH.KHZ_10
- **1 kHz**: BANDWITH.KHZ_1
- **100 Hz**: BANDWITH.HZ_100
- **10 Hz**: BANDWITH.HZ_10