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


from machine import I2C

# Segments to be switched on for characters and digits on 7-Segment Displays
# all zeros is a blank display
# starts from ascii char ! (dec 33 / 0x21)
charTable = [
# !"#$%&'(
0B00000000,0B00000000,0B00000000,0B00000000,0B00000000,0B00000000,0B00100000,0B00000000,
# )%*+,-./
0B00000000,0B00000000,0B00000000,0B00000000,0B00000000,0B00000001,0B00000000,0B00000000,
# 01234567
0B01111110,0B00110000,0B01101101,0B01111001,0B00110011,0B01011011,0B01011111,0B01110000,
# 89:;<=>?
0B01111111,0B01111011,0B00000000,0B00000000,0B00000000,0B00001001,0B00000000,0B01100101,
# @ABCDEFG
0B00000000,0B01110111,0B00011111,0B00001101,0B00111101,0B01001111,0B01000111,0B00000000,
# HIJKLMNO
0B00110111,0B00010000,0B00111000,0B00000000,0B00001110,0B00000000,0B00010101,0B00011101,
# PQRSTUVW
0B01100111,0B01110011,0B00000101,0B00000000,0B00001111,0B00011100,0B00000000,0B00000000,
# XYZ[\]^_
0B00000000,0B00000000,0B00000000,0B01001110,0B01111000,0B00000000,0B00000000,0B00001000,
# `abcdefg
0B00000000,0B01111101,0B00011111,0B00001101,0B00111101,0B01001111,0B01000111,0B00000000,
# hijklmno
0B00010111,0B00010000,0B00011000,0B00000000,0B00001110,0B00000000,0B00010101,0B00011101,
# pqrstuvw
0B01100111,0B01110011,0B00000101,0B00000000,0B00001111,0B00011100,0B00000000,0B00000000,
# xyz{|}~
0B00000000,0B00000000,0B00000000,0B00000000,0B00000000,0B00000000,0B00000000,0B00000000
]

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
    def __init__(self, i2c, address=0x38):
        self.i2c = i2c
        self.address = address  # I2C addres for type A (see data sheet)
        self.decodemode = 0x0F  # all digits get decoded to hexadecimal
        self.digits = 3         # 4 digits display
        self.secondsLeds = 6    # leds used to display seconds on a clock
        self.__i2cTransfer__(OP_DISPLAYTEST,0)
        self.setScanLimit(self.digits)
        self.clearDisplay()
        self.setIntensity(4)
        self.__i2cTransfer__(OP_DECODEMODE,self.decodemode)
        self.shutdown(True)

    # write command and data byte to display
    def __i2cTransfer__(self, opcode, data):
        self.i2c.writeto(self.address, bytes([opcode,data]))

    # start in ClockMode (4 digits, secondsLed1, secondsLed2)
    def ClockMode(self, secondsLed1=1, secondsLed2=2):
        if secondsLed1 < 0 or secondsLed1 > 8 or secondsLed2 < 0 or secondsLed2 > 8:
            return
        self.secondsLeds = ( 1 << secondsLed1 ) | (1 << secondsLed2)
        self.setScanLimit(3)
        self.decodemode = 0x0F
        self.__i2cTransfer__(OP_DECODEMODE,self.decodemode)
        self.clearDisplay()

    # show the time on the display, and flash the seconds leds
    # Params:
    # hour (0-23)
    # minutes (0-59)
    # blink (seconds leds: True = on , False = turn off)
    def setClock(self, hour=0, minutes=1, blink=False):
        if hour < 0 or hour > 23 or minutes < 0 or minutes > 59:
            return
        self.decodemode = 0x0F
        self.__i2cTransfer__(OP_DECODEMODE,self.decodemode)
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

    # Set the number of digits (or rows) to be displayed.
    # See datasheet for sideeffects of the scanlimit on the brightness
    # of the display.
    # Params :
    # limit	number of digits to be displayed (1..4)
    def setScanLimit(self, limit):
        if limit < 0 or limit > 3:
            limit = 3
        self.__i2cTransfer__(OP_SCANLIMIT,limit)
        self.digits = limit

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

    # sets the indivuals segment(s) on a 7 segment-displays
    # params:
    # digit: the position of the digit on the display (0..3)
    # segment: a value where each indivual bit in the value represents
    # a segment on the display (bit 0 is segment A, bit 1 is segment B ...)
    # bit 8 is the digital point
    def setSegment(self, digit, segment):
        if digit < 0 and digit > self.digits:
            return
        self.decodemode = self.decodemode & ~(1<<digit)
        bit8 = digit | (segment & (1 << 7))
        digit += OP_DIGIT0
        self.__i2cTransfer__(OP_DECODEMODE,self.decodemode)
        self.__i2cTransfer__(digit,segment)
        self.__i2cTransfer__(OP_SEGMENTS,bit8)

    # Display a hexadecimal digit on a 7-Segment Display
    # Params:
    # digit	the position of the digit on the display (0..3)
    # value	the value to be displayed. (0x00..0x0F)
    # dp	sets the decimal point.
    def setDigit(self, digit, value, dp=False):
        if digit < 0 or digit > self.digits or value > 15:
            return
        self.decodemode |= ( 1 << digit)
        self.__i2cTransfer__(OP_DECODEMODE, self.decodemode)
        self.__i2cTransfer__(OP_DIGIT0 + digit, value)
        self.__i2cTransfer__(OP_SEGMENTS, self.decodemode)

    # Display a character on a 7-Segment display.
    # There are only a few characters that make sense here :
    #	'0','1','2','3','4','5','6','7','8','9','0',
    #  'A','b','c','d','E','F','H','i','j','l','o','P','Q','r','t',
    #  '-','_',' '
    # Params:
    # digit	the position of the character on the display (0..3)
    # value	the character to be displayed.
    # dp	sets the decimal point.
    def setChar(self, digit, value, dp=False):
        index = ord(value) - 32
        if index > 95 or index < 0:
            index = 95
        v = charTable[index]
        if dp:
            v |= 0B10000000
        self.setSegment(digit,v)
