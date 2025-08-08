# esp32_cyd
## Motivation
I bought a couple of "cheap yellow display" esp32 boards off AliExpress after reading a
[Random Nerd Tutorials write-up](https://randomnerdtutorials.com/cheap-yellow-display-esp32-2432s028r/)
of them and thinking "that sounds cool" since I have a few esp32s floating around my place but I just don't
use them since I like having some nice intuitive inputs and outputs to play with.

Later I read another [RNT article on ESP-NOW networking](https://randomnerdtutorials.com/micropython-esp-now-esp32/) and
got really interested since it looked like it was getting very close to the simplicity of the
[BBC micro:bit's radio code](https://microbit-micropython.readthedocs.io/en/latest/tutorials/radio.html),
which is my gold standard for educational devices and code.

> **Disclaimer:** I'm not a low level kinda guy, so these three libraries are heavily based on two things:
> 1. Prior art - I referred to [this library](https://github.com/rdagger/micropython-ili9341) and the code provided in the [RNT examples](https://randomnerdtutorials.com/micropython-cheap-yellow-display-board-cyd-esp32-2432s028r/). Like half of the code floating around out there, particularly for microcontrollers, I don't know what the provenance is.
> 2. A (un)healthy dose of Anthropic's Claude helping me along the way, sending me down rabbit holes, and very helpfully holding the gun when I want to shoot myself in the foot. This was partly an exercise in specifically seeing if I could get an agent workflow to make something I was happy with whilst touching the code as little as possible, and partly because I knew it would take longer than my attention span to do myself 😅

This is an interesting method of indicating AI involvement from [BadgeAI](https://www.badgeai.org/):  
![Text: T.AI.3](https://img.shields.io/badge/Text-T.AI.3-blue)

## Libraries
There are three libraries here. I'm not making too many assumptions about code quality, but I tried to get the user-facing API
landing in a good spot, striking a bit of a balance between simplicity and flexibility. I wanted to hide a lot of the configuration
details of the hardware - although I guess if you're using different boards there's some poking around to be done under the hood.

### Some technical nerdery
In my experience, students don't cope well with figuring out events and blocking vs non-blocking code. Writing an event loop that does polling
and putting all their reactive code in there is hard enough without wondering why their button press isn't registering because they have a sleep
somewhere gumming up the works. I wanted to avoid that as much as possible with these libraries, so they make heavy use of interrupts and callbacks
populating internal event queues that then get passed on to the user's code.

The `easy_radio` and `easy_touch` both use callbacks and event queues to prevent the need to check for events at just the right time. The radio
populates a message queue of configurable length, so `receive` just checks whether anything is on the queue. The touch library was a bit trickier
to handle since the idea of swipes weren't well supported by hardware, so there's some polling that happens to figure out where longer touches go.
This library maintains an internal state machine for press/release events and a short queue of location history used to determine if there was a
swipe and where it went (which is far from perfect). The `is_touched` method just checks if the last press was recent enough to count, so sort of
cheats in the name of keeping the processing snappy.

### [easy_radio](docs/easy_radio.md)
Simple wireless communication between ESP32 devices using ESP-NOW protocol. Send and receive messages with automatic message queuing, group filtering, and range control - similar to the BBC micro:bit's radio functionality.

**Quick example:**
```python
from easy_radio import Radio
radio = Radio(group=1)
radio.send("Hello World!")
message = radio.receive()
```

[📖 Full easy_radio documentation](docs/easy_radio.md)

### [easy_display](docs/easy_display.md)
Easy-to-use display library for showing text, drawing shapes, and creating simple graphics on the color LCD. Automatically handles text wrapping and provides simple drawing functions.

**Quick example:**
```python
from easy_display import Display
display = Display()
display.show_text("Hello World!")
display.draw_circle(160, 120, 50, color="red")
```

[📖 Full easy_display documentation](docs/easy_display.md)

### [easy_touch](docs/easy_touch.md)
Touch detection library with automatic calibration. Detects taps, swipes, and current touch positions on the resistive touchscreen. Handles coordinate transformation and provides (basic) gesture recognition.

**Quick example:**
```python
from easy_touch import Touch
touch = Touch()  # Auto-calibrates on first use

if touch.was_touched():
    print("Screen was tapped!")
if touch.was_swiped(direction='left'):
    print("Swiped left!")
```

[📖 Full easy_touch documentation](docs/easy_touch.md)
