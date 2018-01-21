# Sensory Box

This project aims to create interactive sensory box for kids.

## Used material

You don't have to use exactly the items linked here, it's just for reference.

* Lunch box
* ESP32 (Lolin32 by Wemos) (([AliExpress](https://www.aliexpress.com/item/WEMOS-LOLIN32-V1-0-0-wifi-bluetooth-board-based-ESP-32-4MB-FLASH/32808551116.html?spm=a2g0s.9042311.0.0.sjiLzG)) - there is newer version available, you can use that, but the pinout might be different
* NeoPixel LED Strip ([AliExpress](https://www.aliexpress.com/item/individually-addressable-1m-5m-waterproof-ip67-ip30-5050-rgb-30-60-144-led-m-5v-ws2811/32578740276.html?spm=a2g0s.9042311.0.0.27EK6W))
* 3x LED Push Button with illumination ring (([AliExpress](https://www.aliexpress.com/item/16mm-Metal-brass-Push-Button-Switch-flat-round-illumination-ring-Momentary-1NO-Car-press-button-pin/32676237694.html?spm=a2g0s.9042311.0.0.4owHGL))
* ON/OFF Switch ([AliExpress](https://www.aliexpress.com/item/Hot-Sale-5Pcs-AC-250V-3A-2-Pin-ON-OFF-I-O-SPST-Snap-in-Mini/32608267264.html?spm=a2g0s.9042311.0.0.4owHGL))
* Joystick ([AliExpress](https://www.aliexpress.com/item/1pc-Free-Shipping-Higher-Quality-Dual-axis-XY-Joystick-Module-PS2-Joystick-Control-Lever-Sensor-For/32630096107.html?spm=a2g0s.9042311.0.0.4owHGL))
* 4x Toggle Switch ([AliExpress](https://www.aliexpress.com/item/Promotion-New-5-Pcs-AC-250V-3A-120V-6A-On-Off-2-Position-Spdt-Self-Locking/32649438609.html?spm=a2g0s.9042311.0.0.4owHGL))
* Rotary Encoder ([AliExpress](https://www.aliexpress.com/item/2pcs-EC11-Rotary-Encoder-Audio-Digital-Potentiometer-with-Switch-Handle-20mm-EC11-Switch/32673684898.html?spm=a2g0s.9042311.0.0.4owHGL))
* Knob for Rotary Encoder ([AliExpress](https://www.aliexpress.com/item/30mm-17mm-Aluminum-DAC-CD-Amplifier-Potentiometer-Volume-Knob-6mm-Knurled-High-Quality-Black-Red-Silver/32811673785.html?spm=a2g0s.9042311.0.0.4owHGL))
* 3x Tactile Push Buttons
* Red, Green, Blue, and White LEDs
* Photo Resistor
* Push Button
* 18650 Battery with holder and JST2.0 connector
* Resistors:
    * 1x 47&Omega;
    * 1x 200&Omega;
    * 2x 470&Omega;
    * 1x 1k&Omega;
    * 2x 10k&Omega;
    * 2x 100k&Omega;
    * 2x 220k&Omega;


## Wiring

The schema is in the `board.fzz` Fritzing file.

## Software

* flash latest version of [MicroPython for ESP32](https://micropython.org/download), I've used `esp32-20180121-v1.9.3-240-ga275cb0f.bin`
* connect to the device, connect to WiFi and install `uasyncio` package:
```
import upip
upip.install('micropython-uasyncio')
```
* upload `main.py` to the device and reboot
