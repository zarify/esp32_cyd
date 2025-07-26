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
> 2. A (un)healthy dose of Anthropic's Claude helping me along the way, sending me down rabbit holes, and very helpfully holding the gun when I want to shoot myself in the foot. Seriously though, this has been my first enjoyable foray into agentic coding.

## Libraries
There are three libraries here. I'm not making too many assumptions about code quality, but I tried to get the user-facing API
landing in a good spot, striking a bit of a balance between simplicity and flexibility. I wanted to hide a lot of the configuration
details of the hardware - although I guess if you're using different boards there's some poking around to be done under the hood.

### easy_radio
The ESP-NOW API is actually pretty good, but I wanted to make this very simple like the micro:bit, and just do broadcast with some light config in
the form of channels, groups, and transmission power.

Import and set up the radio:

```python
from easy_radio import Radio
radio = Radio()
# or for more configuration
# radio = Radio(channel=6, group=5, queue_size=20, tx_power=13)
```

- `channel` is wifi spectrum. Range is 1-13.
- `group` is an artificial filtering method similar to that found in micro:bit radio. Range is 0-255, with 0 being promiscuous mode.
- `queue_size` is the held packet queue. Packets are received by an interrupt-driven internal function.
- `tx_power` is the dBm power of the radio transmission and ranges from 8-20, but I made that a 1-13 value to make it more in line with how the micro:bit does it.

Send a message:

```python
radio.send("G'day")
```

Messages can be up to 248 bytes in length.

Receive a message:

```python
packet = radio.receive()
if packet:
    print("Packet received")
    print(packet["sender"])  # MAC of sender
    print(packet["text"])    # message text
    print(packet["rssi"])    # signal strength of last message
    print(packet["time"])    # ms elapsed since sender boot
    print(packet["group"])   # group of sender
```

Groups can be changed through `set_group(n)` and queried through `get_group()`.

Power can be set through `set_power(n)` and queried through `get_power()`.

Transmission and receipt stats can be queried with `stats()`.

The device's MAC address can be queried through `get_my_address()`

### easy_display
The display is pretty slow and good enough for basic UI or visualisations, but
nothing fancy. The text handling is probably one of the better parts of it.

The library is written with the assumption you're using it in landscape mode
with a 320x240 display.

Import and initialise the display:

```python
from easy_display import Display

display = Display()
```

`show_text(s, color="white", background="black")` takes a single string or a list of strings. Strings will
automatically wrap, and will be displayed from the top-left corner of the display.
Lists of strings will be displayed with one item per line.

`show_text_at(x, y, s, color="white", background="black")` takes a single
single string and shows it at the coordinates with no wrapping.

The following methods do what you expect them to do:
- `draw_pixel(x, y, color="white")`
- `draw_line(x1, y1, x2, y2, color="white")`
- `draw_rectangle(x, y, width, height, color="white", filled=False)`
- `draw_circle(x, y, radius, color="white", filled=False)`
- `draw_ellipse(x, y, width, height, color="white", filled=False)`
- `draw_polygon(points, color="white", filled=False)` - points is a list of (x, y) tuples
- `display_on()`
- `display_off()`
- `sleep(enable=True)`

To try and wring a bit of performance out of this library there's some
optional buffering that can be enabled. Call `begin_drawing()` before you
start, and `end_drawing()` when you finish, and the library will try and
reduce the number of SPI calls (it's still pretty slow though).

### easy_touch
The CYD has a resistive touch screen which isn't too bad. It's a bit of
an annoyance since by default the coordinate system on mine was flipped
and also in portrait mode (like an animal). To make matters worse, the
reported coordinates were off from what you would expect (by quite a lot),
so there was some calibration and normalisation to be done!

Import and initialise:

```python
from easy_touch import Touch

touch = Touch()
```

There are two methods for getting touches, you can poll, or set up
a callback. You should probably set up the callback since it makes things
much easier.

Polling:

```python
pos = touch.get_touch()
if pos:
    print(f"Touch at {pos['x']}, {pos['y']})
```

Callback:

```python
def handle_touch(x, y):
    print(f"Touch at {x}, {y}")

touch = Touch(on_touch=handle_touch)
```

If the `easy_touch` library is used on a system with `easy_display` it
will automatically run through some calibration steps on first run to
figure out the orientation and any coordinate issues that need to be
accounted for. This will involve some tapping of red squares in the
corners for a while.

Calibration data will then be written to a JSON file on the device, so
you won't have to do it again unless you wipe the device. You can also
call the `recalibrate` method to do the whole thing over, or just delete
the JSON file and restart (or call `reset_calibration` which will delete
the file for you).