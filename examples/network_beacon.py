"""
Basic network beacon example using the easy_display and easy_radio libraries.

This script sends out a ping message every 3 seconds and shows the ping
time on the display to verify that a message has been sent.

Pair this with the network_receiver.py example to see the messages along
with basic stats like the group, time received, and RSSI value.
"""

from easy_radio import Radio
from easy_display import Display
import time

display_lines = 240 // 11 - 1 # 240px height
display_buffer = []

display = Display()
radio = Radio(group=5, channel=6)

while True:
    # send out a beacon message every 3 seconds
    radio.send("Ping!")
    # log the ping time in seconds since boot
    current_time = time.ticks_ms() // 1000
    display_buffer.append(f"Ping at {current_time} seconds")
    if len(display_buffer) > display_lines:
        display_buffer.pop(0)  # Keep only the last 'display_lines' entries
    display.show_text(display_buffer, color="white", background="black")
    time.sleep(3)