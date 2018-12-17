# MIT License
#
# Copyright (c) 2018 Andre Peeters (andrethemac)
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

# MAX6958
# https://www.maximintegrated.com/en/products/power/display-power-control/MAX6958.html
# 2-Wire Interfaced (i2c), 3V to 5.5V, 4-Digit, 9-Segment LED Display Driver
# This driver uses a peculiar way to wire the LED display.
# It works great with indivual LED Display's, but not with clockdisplays or
# quad display like these (https://docs.broadcom.com/docs/AV02-0568EN)

# subset of MAX6958.py, just for clocks (4digits and 2 blinking leds for seconds)


from machine import I2C

# the opcodes for the max6958
OP_NOOP = const(0x00)
OP_DECODEMODE = const(0x01)
OP_INTENSITY = const(0x02)
OP_SCANLIMIT = const(0x03)
OP_CONFIGURATION = const(0x04)
OP_DISPLAYTEST = const(0x07)
OP_DIGIT0 = const(0x20)
OP_DIGIT1 = const(0x21)
OP_DIGIT2 = const(0x22)
OP_DIGIT3 = const(0x23)
OP_SEGMENTS = const(0x24)

class MAX6958:
    def __init__(self, i2c, address=0x38, secondsLed1=1, secondsLed2=2):
        if secondsLed1 < 0 or secondsLed1 > 8 or secondsLed2 < 0 or secondsLed2 > 8:
            secondsLed1 = 0
            secondsLed2 = 0
        self.i2c = i2c
        self.address = address  # I2C addres for type A (see data sheet)
        self.secondsLeds = ( 1 << secondsLed1 ) | (1 << secondsLed2)
        self.__i2cTransfer__(OP_DISPLAYTEST,0)
        self.__i2cTransfer__(OP_SCANLIMIT,3)
        self.clearDisplay()
        self.setIntensity(4)
        self.__i2cTransfer__(OP_DECODEMODE,0x0F)
        self.shutdown(True)

    # write command and data byte to display
    def __i2cTransfer__(self, opcode, data):
        self.i2c.writeto(self.address, bytes([opcode,data]))

    # show the time on the display, and flash the seconds leds
    # Params:
    # hour (0-23)
    # minutes (0-59)
    # blink (seconds leds: True = on , False = turn off)
    def setClock(self, hour=0, minutes=1, blink=False):
        if hour < 0 or hour > 23 or minutes < 0 or minutes > 59:
            return
        self.__i2cTransfer__(OP_DIGIT0, hour // 10)
        self.__i2cTransfer__(OP_DIGIT1, hour % 10)
        self.__i2cTransfer__(OP_DIGIT2, minutes // 10)
        self.__i2cTransfer__(OP_DIGIT3, minutes % 10)
        self.__i2cTransfer__(OP_SEGMENTS,self.secondsLeds * blink)

    # Set the shutdown (power saving) mode for the device
    # Params :
    # status	If true the device goes into power-down mode. Set to false
    #		for normal operation.
    def shutdown(self, status=True):
        self.__i2cTransfer__(OP_CONFIGURATION,not(status))

    # Set the brightness of the display.
    # Params:
    # intensity	the brightness of the display. (0..63)
    def setIntensity(self, intensity):
        if intensity < 0 or intensity > 63:
            intensity = 4
        self.__i2cTransfer__(OP_INTENSITY,intensity)

    # Switch all Leds on the display off. (decode mode = 0)
    # show 0's on display (decode mode = 0x0F)
    def clearDisplay(self):
        self.__i2cTransfer__(OP_CONFIGURATION,0x21)
