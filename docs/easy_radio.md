# Easy Radio Library

The Easy Radio library makes wireless communication between ESP32 devices simple and straightforward, similar to the BBC micro:bit's radio functionality. It uses ESP-NOW protocol for fast, reliable communication without needing WiFi networks.

## Quick Start

```python
from easy_radio import Radio

# Create a radio with default settings
radio = Radio()

# Send a message
radio.send("Hello World!")

# Check for messages
message = radio.receive()
if message:
    print(f"Received: {message['text']}")
```

## Basic Setup

### Creating a Radio
```python
# Simple setup (uses default group 1)
radio = Radio()

# Advanced setup with custom settings
radio = Radio(channel=6, group=5, queue_size=20, tx_power=10)
```

**Settings explained:**
- **channel**: WiFi channel (1-13) - all devices must use the same channel to communicate
- **group**: Radio group (1-255) - only devices in the same group will receive messages
- **queue_size**: How many messages to store (default: 10)
- **tx_power**: Transmission power (1-13) - higher numbers = longer range but more battery use

## Sending Messages

```python
# Send a simple text message
radio.send("Hello from device 1!")

# Messages can be up to 248 characters long
radio.send("This is a longer message with more information...")
```

## Receiving Messages

```python
# Check for new messages (doesn't wait)
message = radio.receive()
if message:
    print(f"From: {message['sender']}")     # Device that sent the message
    print(f"Text: {message['text']}")       # The actual message
    print(f"Signal: {message['rssi']}")     # Signal strength (-30 = very strong, -90 = weak)
    print(f"Group: {message['group']}")     # Which group sent the message

# Wait up to 1 second for a message
message = radio.receive(timeout_ms=1000)

# Get all waiting messages at once
all_messages = radio.receive_all()
for msg in all_messages:
    print(f"Message: {msg['text']}")
```

## Radio Groups

Groups let you organize devices so they only receive messages meant for them:

```python
# Join group 5 (only hear from other group 5 devices)
radio.set_group(5)

# Use promiscuous mode (hear from ALL groups)
radio.set_group(0)

# Check which group you're in
current_group = radio.get_group()
print(f"I'm in group {current_group}")
```

## Adjusting Range and Power

```python
# Set transmission power (1 = shortest range, 13 = longest range)
radio.set_power(13)  # Maximum range
radio.set_power(1)   # Minimum power for close devices

# Check current power setting
power = radio.get_power()
print(f"Current power: {power}")
```

## Monitoring Performance

```python
# Get statistics about your radio usage
stats = radio.get_stats()
print(f"Messages sent: {stats['sent']}")
print(f"Messages received: {stats['received']}")
print(f"Errors: {stats['errors']}")

# Find out your device's address
my_address = radio.get_my_address()
print(f"My address: {my_address}")

# Reset statistics
radio.reset_stats()
```

## Common Examples

### Simple Chat Between Two Devices
```python
from easy_radio import Radio
from time import sleep

radio = Radio(group=1)  # Both devices use group 1

while True:
    # Send a message every 5 seconds
    radio.send("Hello from device A!")
    
    # Check for incoming messages
    message = radio.receive()
    if message:
        print(f"Received: {message['text']}")
    
    sleep(5)
```

### Sensor Network with Different Groups
```python
from easy_radio import Radio

# Temperature sensors use group 10
temp_radio = Radio(group=10)

# Humidity sensors use group 20  
humidity_radio = Radio(group=20)

# Base station listens to all groups
base_radio = Radio(group=0)  # Promiscuous mode

# Sensors send data
temp_radio.send("Temperature: 23.5C")
humidity_radio.send("Humidity: 65%")

# Base station receives from all
while True:
    message = base_radio.receive()
    if message:
        print(f"Group {message['group']}: {message['text']}")
```

## Troubleshooting

**No messages received?**
- Check both devices are on the same channel
- Check both devices are in the same group (or one is in group 0)
- Make sure devices are close enough (try higher power)

**Messages being lost?**
- Increase queue_size if many messages arrive quickly
- Check for errors with `radio.get_stats()`

**Short range?**
- Increase tx_power setting
- Check for interference on your channel
