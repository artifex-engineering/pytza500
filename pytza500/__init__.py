# MIT License
#
# Copyright (c) 2025 Artifex Engineering GmbH & Co KG.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import re
import sys
import ftd2xx
from enum import Enum
from time import sleep


class BANDWITH(Enum):
    KHZ_10 = "10 kHz"
    KHZ_1 = "1 kHz"
    HZ_100 = "100 Hz"
    HZ_10 = "10 Hz"

class INITIAL_AUTO_ZERO(Enum):
    NONE = "None"
    AUTO_ZERO = "Auto zero"
    AUTO_ZERO_RESET = "Auto zero reset"

class GAIN(Enum):
    X1 = "x1"
    X10 = "x10"
    X100 = "x100"
    X1000 = "x1000"
    X10000 = "x10000"
    X100000 = "x1000000"
    AUTO = "auto-gain"

class UNITS(Enum):
    NANOAMPERE = "nA"
    MICROAMPERE = "µA"
    MILLIAMPERE = "mA"
    AMPERE = "A"
    NANOWATTS = "nW"
    MICROWATTS = "µw"
    MILLIWATTS = "mW"
    WATTS = "W"

class TZA500():
    def __init__(self) -> None :
        """
        Initializes the TZA500 class.
        """
        self._unit: str = UNITS.MICROAMPERE.value

        self._port: str = ""
        self._device = None

        self._bandwith_steps: dict = {
            "10 kHz": "B1",
            "1 kHz": "B2",
            "100 Hz": "B3",
            "10 Hz": "B4"
        }

        self._gain_steps: dict = {
            "x1": "V1",
            "x10": "V2",
            "x100": "V3",
            "x1000": "V4",
            "x10000": "V5",
            "x100000": "V6",
            "auto-gain": "auto-gain"
        }

        self._units: dict = {
            "nA": "Nanoampere (nA)",
            "µA": "Microampere (µA)",
            "mA": "Milliampere (mA)",
            "A": "Ampere (A)",
            "nW": "Nanowatts (nW)",
            "µW": "Microwatts (µW)",
            "mW": "Milliwatts (mW)",
            "W": "Watts (W)",
        }
        self._sensitivity: float = 1.0
        self._initial_auto_zero: str = INITIAL_AUTO_ZERO.NONE.value
        self._invert_input_polarity: bool = False
        self._bandwith: str = BANDWITH.KHZ_10.value
        self._autogain_gain: int = None
        self._gain: str = GAIN.X1.value
        self._max_gain: int = len(self._gain_steps) - 1

        self._tza_comm_max_retries: int = 800

        self._tza_fw: str = ""
        self._tza_serial: str = ""
        self._tza_date_of_manufacturing: str = ""
    
    @property
    def sensitivity(self) -> float:
        return self._sensitivity
    
    @sensitivity.setter
    def sensitivity(self, value: float) -> None:
        self._sensitivity = value

    @property
    def unit(self) -> str:
        return self._units[self._unit]
    
    @property
    def initial_auto_zero(self) -> str:
        return self._initial_auto_zero
    
    @property
    def invert_input_polarity(self) -> str:
        return self._invert_input_polarity

    @property
    def tza_firmware_version(self) -> str:
        return self._tza_fw
    
    @property
    def tza_serial_number(self) -> str:
        return self._tza_serial
    
    @property
    def tza_date_of_manufacturing(self) -> str:
        return self._tza_date_of_manufacturing
    
    @staticmethod
    def find_devices() -> list[str]:
        """
        Return list of found devices

        :result:
            found_devices(list[str]): list of found TZA500 devices
        """
        devices_found = []

        if sys.platform != "win32":
            ftd2xx.setVIDPID(0x0403, 0x9a68) # For linux and macOS

        numDevs = ftd2xx.createDeviceInfoList()

        for i in range(0, numDevs):
            dev = ftd2xx.getDeviceInfoDetail(i)
            if "TZA500" in dev["description"].decode(errors="ignore"):
                devices_found.append("{} - {}".format(dev["description"].decode(errors="ignore"), dev["serial"].decode(errors="ignore")))

        return devices_found
    
    def connect(self, device: str) -> None:
        """
        Connects to TZA500 and initializes it

        :param:
            device(str): Device string in the format "TZA500 - serial_number" E.g. "TZA500 - 12345"
        
        :return:
            result(bool): Returns whether the device was successfully connected and initialized.
        """

        if self._device != None:
            return False

        if device == "":
            raise Exception("No port selected.")
        self._port = device.split("- ")[1]

        # Open device
        try:
            self._device = ftd2xx.openEx(self._port.encode())
            self._device.setBaudRate(115200)
            self._device.setDataCharacteristics(8, 0, 0) # 8 data bits, 1 stop bit, no parity
            self._device.setFlowControl(0, 0, 0) # No flow control
            self._device.setTimeouts(1000, 0)
            self._device.setChars(126, 1, 0, 0)
            self._device.resetDevice()
            self._device.purge() # Purge receive/transmit buffers
        except ftd2xx.DeviceError:
            raise Exception("Cannot open Device with serial number {}.".format(self._port))
        
        self._tza_send("$U")
        if self._tza_recv() != "U OK":
            self.disconnect()
            return False

        if not self._initialize():
            self.disconnect()
            return False
        return True
    
    def _tza_send(self, msg: str):
        if self._device is None:
            raise Exception("Send error: port not open.")
        self._device.purge() # Purge receive/transmit buffers
        self._device.write(msg.encode())
    
    def _tza_recv(self) -> str:
        if self._device is None:
            raise Exception("Recive error: port not open.")
        msg = b""
        i = 0
        while i < self._tza_comm_max_retries:
            if self._device.getQueueStatus() > 0: # Check if bytes in buffer
                msg = self._device.read(self._device.getQueueStatus()) # Read entire buffer
                while not msg.endswith(b'\r'): # Append buffer until '\r' is found
                    msg += self._device.read(self._device.getQueueStatus())
                
                return msg.decode(errors="ignore").replace("\r", '').strip()
            sleep(0.01)
            i += 1
        raise TimeoutError("No Valid Data received.")

    def _initialize(self) -> bool:
        info = self.tza_get_info()

        if re.sub(r"^(tza500)(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE) != "TZA500":
            return False

        regex_fw = re.sub(r"^tza500.*fw.*?([0-9]*\.[0-9]*)(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE)
        regex_serial = re.sub(r"(?:\n|.*$)*serial:.*?([0-9]+)(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE)
        regex_date_of_manufacturing = re.sub(r"(?:\n|.*$)*date of manufacturing:.*?([0-9]{1,2}/[0-9]{2,4})(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE)

        self._tza_fw = regex_fw if regex_fw != info else "" # Get TZA500 Firmware version

        self._tza_serial = regex_serial if regex_serial != info else "" # Get TZA500 serial number
        self._tza_date_of_manufacturing = regex_date_of_manufacturing if regex_date_of_manufacturing != info else "" # Get TZA500 date of Manufacturing

        if not self.tza_set_auto_zero_reset():
            self.disconnect()
            return False
    
        # Set default values
        if not self.tza_set_gain(self._gain):
            return False

        return True

    def tza_get_info(self) -> str:
        """
        Returns the device info as a printable string.

        :return:
            info(str): Printable device info
        """
        self._tza_send("$I")
        return self._tza_recv()
    
    def set_unit(self, unit: UNITS) -> bool:
        """
        Sets the specified unit as the unit used for measurements.

        :param:
            unit(UNITS): Unit to use for measurements
        
        :return:
            result(bool): Returns whether the unit was set successfully
        """
        if unit not in UNITS:
            return False
        self._unit = unit.value
        return True
    
    def tza_is_polarity_inverted(self) -> bool | None:
        """
        Returns whether the polarity is inverted or not.

        :return:
            is_polarity_inverted(bool): True if the polarity is inverted
        """
        self._tza_send("$F")
        received = self._tza_recv()

        if received == "F0":
            self._invert_input_polarity = False
            return False
        elif received == "F1":
            self._invert_input_polarity = True
            return True
        else:
            return None
    
    def tza_set_polarity(self, invert_polarity: bool) -> bool:
        """
        Sets whether the polarity should be inverted or not.

        :param:
            invert_polarity(bool): Whether the polarity should be inverted or not
        
        :return:
            result(bool): Returns whether the polarity was set successfully
        """
        invert_polarity = bool(invert_polarity)

        polarity_command = "N" if invert_polarity == False else "C"
        
        self._tza_send("${}".format(polarity_command))

        recv = self._tza_recv()
        if recv == "{} OK".format(polarity_command):
            self._invert_input_polarity = invert_polarity
            return True
        return False
    
    def tza_get_bandwith(self) -> str | None:
        """
        Returns the current bandwith.

        :return:
            bandwith(str): Current bandwith in format: 10 kHz, 1 kHz, ...
        """
        self._tza_send("B?")
        received = self._tza_recv()

        if received in self._bandwith_steps.values():
            self._bandwith = dict(zip(self._bandwith_steps.values(), self._bandwith_steps.keys()))[received]
            return self._bandwith
        return None
    
    def tza_set_bandwith(self, bandwith: str | BANDWITH) -> bool:
        """
        Sets the specified bandwith.

        :param:
            bandwith(str | BANDWITH): Bandwith to set
        
        :return:
            result(bool): Returns whether the bandwith was set successfully
        """
        if type(bandwith) == BANDWITH:
            bandwith = str(bandwith.value)

        if bandwith not in self._bandwith_steps.keys():
            raise Exception("Invalid bandwith. choose one from the pre-defined bandwiths.")
        
        self._tza_send(self._bandwith_steps[bandwith])
        recv = self._tza_recv()
        if recv == "{} OK".format(self._bandwith_steps[bandwith]):
            self._bandwith = bandwith
            return True
        return False

    def tza_get_gain(self) -> str | None:
        """
        Returns the current gain.

        :return:
            gain(str): Current gain in format: x1, x10, ...
        """
        self._tza_send("V?")
        received = self._tza_recv()
        
        gain = received.splitlines()
        if gain[0] == "V? OK" and gain[1] in self._gain_steps.values():
            if self._gain != "auto-gain":
                self._gain = dict(zip(self._gain_steps.values(), self._gain_steps.keys()))[gain[1]]
            self._autogain_gain = int(self._gain_steps[dict(zip(self._gain_steps.values(), self._gain_steps.keys()))[gain[1]]][1:])
            return ("Auto: " if self._gain == "auto-gain" else "") + dict(zip(self._gain_steps.values(), self._gain_steps.keys()))[gain[1]]
        return None
    
    def tza_set_gain(self, gain: str | GAIN) -> bool:
        """
        Sets the specified gain.

        :param:
            gain(str | GAIN): Gain to set
        
        :return:
            result(bool): Returns whether the gain was set successfully
        """
        if type(gain) == GAIN:
            gain = str(gain.value)

        if gain not in self._gain_steps.keys():
            raise Exception("Invalid gain. choose one from the pre-defined gains.")

        if gain == "auto-gain":
            self._gain = gain
            return True
        
        self._tza_send(self._gain_steps[gain])
        recv = self._tza_recv()
        if recv == "{} OK".format(self._gain_steps[gain]):
            if self._gain != "auto-gain":
                self._gain = gain
            self._autogain_gain = int(self._gain_steps[gain][1:])
            return True
        return False

    def tza_set_auto_zero(self) -> bool:
        self._tza_send("$A")
        
        recv = self._tza_recv()
        if recv.count("Gain: ") > 0:
            self._initial_auto_zero = INITIAL_AUTO_ZERO.AUTO_ZERO.value
            self._max_gain = int(recv[-1])
            sleep(0.2)
            return True
        elif recv.count("A OK") > 0:
            self._initial_auto_zero = INITIAL_AUTO_ZERO.AUTO_ZERO.value
            self._max_gain = len(self._gain_steps) - 1
            sleep(0.5)
            return True
        return False
    
    def tza_set_auto_zero_reset(self) -> bool:
        self._tza_send("$R")

        recv = self._tza_recv()
        if recv == "R OK":
            self._initial_auto_zero = INITIAL_AUTO_ZERO.AUTO_ZERO.value
            self._max_gain = len(self._gain_steps) - 1
            sleep(0.05)
            return True
        return False

    def _tza_autogain(self, tmp_amplitude: str, recursion: int = 0, last_operation: int = 0) -> str:
        """
        This function automatically adjusts the gain by checking whether the
        measured value is too high or too low and then setting a new gain until
        the measured value is within a valid range.
        """
        if recursion >= len(self._gain_steps):
            return tmp_amplitude
        
        if self._autogain_gain is None:
            self.tza_get_gain() # Get gain as int if not already set

        amplitude = float(tmp_amplitude[:-2].replace(",", "."))

        level = 0.0

        # To calculate if the gain needs to be moved up or down:
        # The maximum output value in percent of each gain level is represented by the numbers (122.85, 12.285, ...)
        #
        # 1. Convert the measure amplitude into percent:
        #    if gain 1: amplitude / 122.85
        #    if gain 2: amplitude / 12.285
        #    if gain 3: amplitude / 1.2285
        #    if gain 4: amplitude / 122.85
        #    if gain 5: amplitude / 12.285
        #    if gain 6: amplitude / 1.2285
        # 2. If the value in percent is above 90 and the set gain level is greater than 1, set the new gain to gain - 1.
        #    If the value in percent is below 8 and the set gain level is lower than 5, set new gain to gain + 1

        if self._autogain_gain == 1:
            level = amplitude / 122.85
        elif self._autogain_gain == 2:
            level = amplitude / 12.285
        elif self._autogain_gain == 3:
            level = amplitude / 1.2285
        elif self._autogain_gain == 4:
            level = amplitude / 122.85 # This is not a typo
        elif self._autogain_gain == 5:
            level = amplitude / 12.285 # This is not a typo
        elif self._autogain_gain == 6:
            level = amplitude / 1.2285 # This is not a typo

        if level > 90.0 and self._autogain_gain > 1:
            self._autogain_gain -= 1
            self.tza_set_gain(dict(zip(self._gain_steps.values(), self._gain_steps.keys()))["V{}".format(self._autogain_gain)]) # Set new gain
            return self._tza_autogain(self.tza_get_single_raw_measure(), recursion + 1, 1) # Return new measurement or re-adjust gain
        elif level < 8.0 and self._autogain_gain < self._max_gain:
            if last_operation == 1: # Prevent jumping between two gain leves
                recursion = len(self._gain_steps)
            self._autogain_gain += 1
            self.tza_set_gain(dict(zip(self._gain_steps.values(), self._gain_steps.keys()))["V{}".format(self._autogain_gain)]) # Set new gain
            return self._tza_autogain(self.tza_get_single_raw_measure(), recursion + 1, 2) # Return new measurement or re-adjust gain
        else:
            return tmp_amplitude

    def tza_get_single_raw_measure(self) -> str:
        """
        Returns a single raw measurement result in the format: I1,0nA or I1,0uA

        :return:
            measurement(str): Raw measurement value in the format: I1,0nA or I1,0uA
        """
        self._tza_send("$E")
        return self._tza_recv()[1:].strip() # Remove 'I' prefix from response

    def tza_get_measurement(self) -> list[float, str]:
        """
        This function returns a single measurement value in the selected unit..

        :return:
            list[value(float): Measured value, unit(str): Selected unit]
        """
        amplitude = self.tza_get_single_raw_measure()
        if self._gain == "auto-gain": # Adjust gain if auto-gain is chosen
            amplitude = self._tza_autogain(amplitude)
        unit = amplitude[amplitude.find("A")-1:] # Get unit from last two bytes of the response

        amplitude = amplitude[:-2].replace(",", ".")
        amplitude = float(amplitude)

        if unit == "uA":
            amplitude *= 1000 # Convert µA to nA

        sensitivity = 1.0
        if self._unit not in ["nA", "µA", "mA", "A"]:
            sensitivity = self._sensitivity
        
        amplitude = amplitude / sensitivity
        
        if self._unit.startswith("n"):
            amplitude = round(amplitude, 3)
        elif self._unit.startswith("µ"):
            amplitude /= 1000 # Nano to micro
            amplitude = round(amplitude, 6)
        elif self._unit.startswith("m"):
            amplitude /= 1000000 # Nano to milli
            amplitude = round(amplitude, 9)
        else:
            amplitude /= 1000000000 # For A and W
            amplitude = round(amplitude, 12)

        return [amplitude, self._unit]
    
    def disconnect(self) -> None:
        """
        Disconnects the connected device.
        """
        if self._device is not None:
            self._device.close()
            self._device = None
        self.__init__()
