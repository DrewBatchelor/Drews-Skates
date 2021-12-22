"""
LED Roller Skates by Drew Batchelor 2021 Version 1.0 RC1
HEAVILY based on the:
LED Ukulele with Feather Sense and PropMaker Wing
Follow the amazing tutorial here:
https://learn.adafruit.com/light-up-reactive-ukulele
Adafruit invests time and resources providing this open source code.
Please support Adafruit and open source hardware by purchasing
products from Adafruit!
Written by Erin St Blaine & Limor Fried for Adafruit Industries
Copyright (c) 2019-2020 Adafruit Industries
Licensed under the MIT license.
All text above must be included in any redistribution.

Code:
copy this code to the board and name it "code.py"
Be sure to have all the libraries "import" on the board in the lib folder 

Hardware:
Adafruit Bluefruit Sense Feather Board
Battery with a switch to control power
Connect 2 Neopixel LED strips to Pin D13, gnd and Battery positive, currently set as 34 Pixels long 2 strips in parallel
Use Adafruit Bluefruit Connect App on Phone to control.
Board buttons: User button will cycle the modes, reset will reset the board. 

Instructions for App:
Connect to: "Drews Skates"
Go to Controller > Control Pad
1 = on / off, 
2 = Change LED pattern 
3 = strobe 
4 = strobe on knock (uses the accelerometer on the board)
Up/Down = LED brightness
Left/Right = LED pattern speed
"""

import time
import array
import digitalio
import board
import neopixel
import random
from digitalio import DigitalInOut, Direction, Pull
import adafruit_lsm6ds.lsm6ds33
from adafruit_led_animation.helper import PixelMap
from adafruit_led_animation.sequence import AnimationSequence
from adafruit_led_animation.group import AnimationGroup
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.color import colorwheel
from adafruit_led_animation.color import (
    BLACK, RED, ORANGE, BLUE, PURPLE, WHITE,
    )

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.button_packet import ButtonPacket
from adafruit_bluefruit_connect.color_packet import ColorPacket

MAX_BRIGHTNESS = 1.0  # set brightness for non-reactive mode
BRIGHTNESS = 0.5  # set brightness for non-reactive mode
brightness_inc = 0.1
VOLUME_CALIBRATOR = 50  # multiplier for brightness mapping
ROCKSTAR_TILT_THRESHOLD = 200  # shake threshold

# Set to the length in seconds for the animations
POWER_ON_DURATION = 1.6
ROCKSTAR_TILT_DURATION = 1

NUM_PIXELS = 34  # Number of pixels used in project
NEOPIXEL_PIN = board.D13
POWER_PIN = board.D10
RATE = 0
TSLEEP = 0.1
STEPSIZE = 1
TEMPO = 0.1
tempo_inc = 0.2

enable = digitalio.DigitalInOut(POWER_PIN)
enable.direction = digitalio.Direction.OUTPUT
enable.value = False

btn = DigitalInOut(board.SWITCH)
btn.direction = Direction.INPUT
btn.pull = Pull.UP

i2c = board.I2C()

pixels = neopixel.NeoPixel(NEOPIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS,
                           auto_write=False)
pixels.fill(0)  # NeoPixels off on startup
pixels.show()

ble = BLERadio()
uart_service = UARTService()
advertisement = ProvideServicesAdvertisement(uart_service)
ble.name = "Drews-Skates" # Bluetooth Name

# PIXEL MAPS: Used for reordering pixels so the animations can run diff config.
# My LED strips start at back outside of the skates, run towards the front, then
# back down the inside.

pixel_map_reverse = PixelMap(pixels, [
    0, 33, 1, 32, 2, 31, 3, 30, 4, 29, 5, 28, 6, 27, 7, 26, 8, 25, 9, 24, 10,
    23, 11, 22, 12, 21, 13, 20, 14, 19, 15, 18, 16, 17], individual_pixels=True)
# Starts at back, goes along both sides at once

pixel_map_fwd = PixelMap(pixels, [
    16, 17, 15, 18, 14, 19, 13, 20, 12, 21, 11, 22, 10,
    23, 9, 24,  8, 25, 7, 26, 6, 27, 5, 28, 4, 29, 3, 30, 2, 31, 1, 32, 0, 33,
    ], individual_pixels=True)
# Starts at the front and goes to back

pixel_map_around = PixelMap(pixels, [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33], individual_pixels=True)
# back Outside to front, then to back down the inside

pixel_map_radiate = PixelMap(pixels, [
    8, 26, 9, 27, 7, 25, 10, 28, 6, 24, 11, 29, 5, 23, 12, 30, 4, 22, 13, 31,
    3, 21, 14, 32, 2, 20, 15, 33, 1, 19, 16, 0, 18, 17], individual_pixels=True)
# 3 Starting at the middles radiate to the front and back

pixel_map = [
    pixel_map_reverse,
    pixel_map_fwd,
    pixel_map_around,
    pixel_map_radiate,
]

# Set up accelerometer
sensor = adafruit_lsm6ds.lsm6ds33.LSM6DS33(i2c)
NUM_SAMPLES = 256
samples_bit = array.array('H', [0] * (NUM_SAMPLES+3))

def power_on(duration):
    #Animate NeoPixels for power on.
    start_time = time.monotonic()  # Save start time
    while True:
        elapsed = time.monotonic() - start_time  # Time spent
        if elapsed > duration:  # Past duration?
            break  # Stop animating
        powerup.animate()

def rockstar_tilt(duration):
    """  Tilt animation - lightning effect with a rotating color
    :param duration: duration of the animation, in seconds (>0.0)
    """
    tilt_time = time.monotonic()  # Save start time
    while True:
        elapsed = time.monotonic() - tilt_time  # Time spent
        if elapsed > duration:  # Past duration?
            break  # Stop animating
        pixels.brightness = MAX_BRIGHTNESS
        pixels.fill(TILT_COLOR)
        pixels.show()
        time.sleep(0.01)
        pixels.fill(BLACK)
        pixels.show()
        time.sleep(0.03)
        pixels.fill(WHITE)
        pixels.show()
        time.sleep(0.02)
        pixels.fill(BLACK)
        pixels.show()
        time.sleep(0.005)
        pixels.fill(TILT_COLOR)
        pixels.show()
        time.sleep(0.01)
        pixels.fill(BLACK)
        pixels.show()
        time.sleep(0.03)

# Cusomize LED Animations  ----------------------------------------------------
powerup = Comet(pixel_map[3], speed=0.01, color=ORANGE, tail_length=40, bounce=True)
rainbow = Rainbow(pixel_map[1], speed=0, period=5*TEMPO+0.5,
                  name="rainbow", step=7.5)
rainbow_chase = RainbowChase(pixel_map[1], speed=TEMPO*0.1, size=4, spacing=15,
                             step=STEPSIZE*10)
rainbow_chase2 = RainbowChase(pixel_map[2], speed=TEMPO*0.1, size=10,
                              spacing=1, step=STEPSIZE*18)
chase = Chase(pixel_map[2], speed=TEMPO*0.3, color=RED, size=1, spacing=3)
rainbow_comet = RainbowComet(pixel_map[2], speed=TEMPO*0.1, tail_length=32,
                             bounce=True)
rainbow_comet2 = RainbowComet(pixel_map[0], speed=TEMPO*0.5, tail_length=64,
                              colorwheel_offset=80, bounce=True)
rainbow_comet3 = RainbowComet(
    pixel_map[1], speed=TEMPO*0.1, tail_length=25, colorwheel_offset=80,
    step=STEPSIZE*4, bounce=False)
strum = RainbowComet(
    pixel_map[3], speed=TEMPO*0.1, tail_length=25, bounce=False,
    colorwheel_offset=50, step=STEPSIZE*4)
lava = Comet(pixel_map[3], speed=TEMPO*0.1, color=ORANGE, tail_length=40, bounce=False)
sparkle = Sparkle(pixel_map[0], speed=0.01, color=BLUE, num_sparkles=10)
sparkle2 = Sparkle(pixel_map[1], speed=0.05, color=PURPLE, num_sparkles=4)

# Animations Playlist - reorder as desired. AnimationGroups play at the same time
animations = AnimationSequence(
    rainbow,
    rainbow_chase,
    rainbow_chase2,
    chase,
    lava,
    rainbow_comet,
    rainbow_comet2,
    AnimationGroup(
        sparkle, strum,
        sparkle, strum,
        ),
    AnimationGroup(
        sparkle2, rainbow_comet3,
        ),
    auto_clear=True,
    auto_reset=True,
)

# Start up
LASTMODE = 1  # start up 
enable.value = True
power_on(POWER_ON_DURATION)  # Power up
MODE = LASTMODE
ROCKSTAR_EN = False
ble.start_advertising(advertisement)

# Main loop
while True:
    if uart_service.in_waiting:
        packet = Packet.from_stream(uart_service)
        if isinstance(packet, ColorPacket):
            # Set all the pixels to one color and stay there.
            pixels.fill(packet.color)
            pixels.show()
        elif isinstance(packet, ButtonPacket):
            if packet.pressed:
                if packet.button == ButtonPacket.BUTTON_1:
                    if not MODE == 0:
                        MODE = 0
                    else:
                        MODE = 1
                    # Toggle sleep mode
                elif packet.button == ButtonPacket.BUTTON_2:
                    animations.next()
                    time.sleep(0.1)
                    #  Next animation
                elif packet.button == ButtonPacket.BUTTON_3:
                    MODE = 2
                    # Dazzle me (temp overrides ROCKSTAR_EN)
                elif packet.button == ButtonPacket.BUTTON_4:
                    ROCKSTAR_EN = not ROCKSTAR_EN
                    # Toggles the Accelermeter dazzle function

            # change the speed of the animation by incrementing offset
                elif packet.button == ButtonPacket.LEFT:
                    TEMPO = min(TEMPO + tempo_inc, 1.0)
                    # TEMPO Highest value is 1 its backwards, higher is
                    # slower effect...sorry, not sorry
                    # TEMPO=1 <-was used for debugging
                    # rainbow.period=5*TEMPO+0.5
                    # Arrg, line above doesn't work
                    rainbow_chase.speed = TEMPO*0.05
                    rainbow_chase2.speed = TEMPO*0.1
                    chase.speed = TEMPO*0.3
                    rainbow_comet.speed = TEMPO*0.1
                    rainbow_comet2.speed = TEMPO*0.5
                    rainbow_comet3.speed = TEMPO*0.1
                    strum.speed = TEMPO*0.1
                    lava.speed = TEMPO*0.1

                elif packet.button == ButtonPacket.RIGHT:
                    TEMPO = max(TEMPO - tempo_inc, 0.0)
                    # TEMPO lowest value is 0 for fastest effects
                    # TEMPO = 0  <-was used for debugging
                    # rainbow.period=5*TEMPO+0.5
                    # Arrg, line above doesn't work
                    rainbow_chase.speed = TEMPO * 0.05
                    rainbow_chase2.speed = TEMPO * 0.1
                    chase.speed = TEMPO*0.3
                    rainbow_comet.speed = TEMPO*0.1
                    rainbow_comet2.speed = TEMPO*0.5
                    rainbow_comet3.speed = TEMPO*0.1
                    strum.speed = TEMPO*0.1
                    lava.speed = TEMPO*0.1

                elif packet.button == ButtonPacket.DOWN:
                    BRIGHTNESS = max(BRIGHTNESS - brightness_inc, 0.0)
                    pixels.brightness = BRIGHTNESS

                elif packet.button == ButtonPacket.UP:
                    BRIGHTNESS = min(BRIGHTNESS + brightness_inc, 1.0)
                    pixels.brightness = BRIGHTNESS

    if MODE == 0:  # If currently off...
        enable.value = False
        pixels.fill(BLACK)
        pixels.show()
        time.sleep(0.5)

    elif MODE >= 1:  # If not OFF MODE...
        if not btn.value:
            animations.next()
            # Read accelerometer
            time.sleep(0.2)

        if ROCKSTAR_EN:
            x, y, z = sensor.acceleration
            accel_total = x * x + y * y  # x=tilt, y=rotate
            # print (accel_total)
            if accel_total > ROCKSTAR_TILT_THRESHOLD:
                MODE = 2
                # print("Tilted: ", accel_total)

        if MODE == 1:
            # time.sleep(2)
            animations.animate()

        elif MODE == 2:
            TILT_COLOR = colorwheel(random.randrange(0, 255, 1))
            rockstar_tilt(ROCKSTAR_TILT_DURATION)
            MODE = LASTMODE
