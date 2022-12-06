# Drews-Skates

## Circuit Python LED Roller Skates 
by Drew Batchelor 2021-2022 
Version 1.0 RC1
Heavily based on the: 

## Adafruit LED Ukulele with Feather Sense and PropMaker Wing
Follow the amazing tutorial here:
https://learn.adafruit.com/light-up-reactive-ukulele

Original Ukulele Code is here:
https://github.com/adafruit/Adafruit_Learning_System_Guides/tree/main/Ukulele

"Adafruit invests time and resources providing this open source code. 
Please support Adafruit and open source hardware by purchasing products from Adafruit! 
Written by Erin St Blaine & Limor Fried for Adafruit Industries <--Thank you! 
Copyright (c) 2019-2020 Adafruit Industries. 
Licensed under the MIT license. 
All text above must be included in any redistribution."

## Code:
Copy this code to the board and name it "code.py". 
Be sure to have all the libraries listed in the "import" on the board in the lib folder. 

## 3D Printed Housing:
Top, Bottom and Button cover 3MF files for printing on an FDM 3D printer. You will also need 4 small Philips self tapping screws M2 by about 8mm length.
The original is modelled in Solidworks, if you need that - please message me.

## Hardware:
Adafruit Bluefruit Sense Feather Board. 
Battery with a switch to control power. 
Connect 2 Neopixel LED strips to Pin D13, ground and battery positive, its currently set up as 34 Pixels long 2 strips in parallel. 
I used some nice flexible silicone wire that was intended for 3.5mm stereo audio connection.
Use Adafruit Bluefruit Connect App on Phone to control. 
Board buttons: User button will cycle the modes, reset will reset the board. 

## Instructions for Adafruit Bluefruit App:
Connect to: "Drews Skates"
Go to Controller > Control Pad
1 = on / off, 
2 = Change LED pattern, 
3 = strobe,  
4 = strobe on knock (uses the accelerometer on the board),
Up/Down = LED brightness,
Left/Right = LED pattern speed.
