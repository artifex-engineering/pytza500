from pytza500 import TZA500, GAIN, UNITS, BANDWITH

devices = TZA500.find_devices() # Get all available devices
print("Available Devices: {}\n\n".format(", ".join(devices) if len(devices) > 0 else "None"))

tza = TZA500() # Create TZA500 instance
tza.connect(devices[0]) # Connect to first device in list

print("Firmware version: {}".format(tza.tza_firmware_version))
print("Serial number: {}".format(tza.tza_serial_number))
print("Date of manufacturing: {}".format(tza.tza_date_of_manufacturing))

print("Device info:\n{}\n\n".format(tza.tza_get_info()))


tza.tza_set_polarity(False) # Set polarity to not inverted
print("Polarity inverted: {}\n\n".format(tza.tza_is_polarity_inverted())) # Print whetever poalrity is inverted or not

tza.tza_set_auto_zero()
print("Initial auto zero: {}".format(tza.initial_auto_zero)) # Print Initial auto zero

tza.tza_set_auto_zero_reset()
print("Initial auto zero: {}\n\n".format(tza.initial_auto_zero)) # Print Initial auto zero


tza.tza_set_bandwith(BANDWITH.KHZ_10) # Set bandwith to 100 kHz
tza.tza_set_gain(GAIN.X1) # Set gain

print("Current bandwith: {}".format(tza.tza_get_bandwith())) # Print current bandwith
print("Current gain: {}".format(tza.tza_get_gain())) # Print current gain

tza.set_unit(UNITS.MICROAMPERE) # Set unit to use in measurements
print("Current Unit: {}".format(tza.unit))

tza.sensitivity = 1.0 # Set sensitivity
print("Current sensitivity: {}\n\n".format(tza.sensitivity)) # Print sensitivity


print("Raw measurement value: ".format(tza.tza_get_single_raw_measure())) # Get direct measurement value from device

measurement_value = tza.tza_get_measurement() # Get measurement value in specified unit
print("Measurement Value: {} {}\n\n".format(measurement_value[0], measurement_value[1])) # measurement value in specified unit

tza.tza_set_gain(GAIN.AUTO) # Set auto gain
print("Current gain: {}".format(tza.tza_get_gain())) # Print current gain

measurement_value = tza.tza_get_measurement() # Get measurement value in specified unit
print("Measurement Value: {}{}\n\n".format(measurement_value[0], measurement_value[1])) # measurement value in specified unit