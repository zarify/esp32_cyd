# Easy Touch Library

The Easy Touch library makes it simple to detect finger touches, taps, and swipes on the ESP32-CYD's touchscreen. It automatically handles calibration and provides easy-to-use methods for detecting different types of touch gestures.

## Quick Start

```python
from easy_touch import Touch

# Create touch interface (automatically calibrates on first use)
touch = Touch()

while True:
    # Check if screen is currently being touched
    current_touch = touch.is_touched()
    if current_touch:
        x, y = current_touch['x'], current_touch['y']
        print(f"Touching at {x}, {y}")
    
    # Check for completed taps
    if touch.was_touched():
        print("Screen was tapped!")
```

## Basic Setup

```python
from easy_touch import Touch

# Simple setup (auto-calibrates if needed)
touch = Touch()

# Advanced setup with custom display size
touch = Touch(width=320, height=240)
```

**First Time Setup:**
When you first use the touch library, it will automatically run a calibration process if you have the display library available. You'll see crosshairs appear on screen - touch the center of each crosshair when prompted. This only needs to be done once.

## Types of Touch Detection

### Current Touch (Real-time)

```python
# Check if screen is being touched right now
current_touch = touch.is_touched()
if current_touch:
    x = current_touch['x']  # X coordinate (0-319)
    y = current_touch['y']  # Y coordinate (0-239)
    print(f"Currently touching at {x}, {y}")
else:
    print("Not touching")
```

### Tap Detection (Press and Release)

```python
# Check if a tap happened since last check
if touch.was_touched():
    coords = touch.get_last_touch_coords()
    x, y = coords
    print(f"Tapped at {x}, {y}")

# Count total taps (like micro:bit button presses)
tap_count = touch.get_touches()
if tap_count > 0:
    print(f"Total taps since last check: {tap_count}")
```

### Swipe Detection

```python
# Check for swipes in specific directions
if touch.was_swiped(direction='left'):
    print("Swiped left!")

if touch.was_swiped(direction='right'):
    print("Swiped right!")

if touch.was_swiped(direction='up'):
    print("Swiped up!")

if touch.was_swiped(direction='down'):
    print("Swiped down!")

# Check for any swipe (any direction)
if touch.was_swiped():
    print("Some kind of swipe detected!")
```

### Area-Specific Swipe Detection

```python
# Only detect swipes in a specific area
# Format: (x, y, width, height)
top_left_area = (0, 0, 160, 120)      # Top-left quarter of screen
bottom_right_area = (160, 120, 160, 120)  # Bottom-right quarter

if touch.was_swiped(bounds=top_left_area):
    print("Swiped in top-left area!")

if touch.was_swiped(bounds=bottom_right_area):
    print("Swiped in bottom-right area!")
```

## Managing Touch History

```python
# Clear all stored touch events (useful for menus/games)
touch.clear_touch_history()

# This resets all the was_touched() and was_swiped() flags
# Use this when switching between different screens or modes
```

## Advanced Calibration

### Manual Calibration

```python
# Force a new calibration (if touch seems inaccurate)
touch.force_calibration()

# Set calibration values manually (advanced users)
touch.calibrate(x_min=100, x_max=1962, y_min=100, y_max=1900)
```

### Testing Touch Accuracy

```python
# Test raw touch coordinates (for debugging)
raw_coords = touch.get_raw_coordinates()
if raw_coords:
    print(f"Raw touch: {raw_coords}")

# Debug touch hardware
touch.debug_touch_hardware()
```

## Common Examples

### Simple Paint Program

```python
from easy_touch import Touch
from easy_display import Display

touch = Touch()
display = Display()

display.clear()
display.show_text("Touch to draw!")

while True:
    current_touch = touch.is_touched()
    if current_touch:
        x, y = current_touch['x'], current_touch['y']
        display.draw_pixel(x, y, color="white")
```

### Button Interface

```python
from easy_touch import Touch
from easy_display import Display

touch = Touch()
display = Display()

# Draw buttons
button1_area = (50, 50, 100, 60)   # x, y, width, height
button2_area = (170, 50, 100, 60)

display.clear()
display.draw_rectangle(50, 50, 100, 60, color="green")
display.show_text_at(70, 75, "Button 1", color="white")
display.draw_rectangle(170, 50, 100, 60, color="blue")
display.show_text_at(190, 75, "Button 2", color="white")

while True:
    if touch.was_touched():
        x, y = touch.get_last_touch_coords()
        
        # Check which button was pressed
        if 50 <= x <= 150 and 50 <= y <= 110:
            print("Button 1 pressed!")
        elif 170 <= x <= 270 and 50 <= y <= 110:
            print("Button 2 pressed!")
```

### Swipe Navigation

```python
from easy_touch import Touch

touch = Touch()
current_page = 1
max_pages = 5

while True:
    if touch.was_swiped(direction='left'):
        if current_page < max_pages:
            current_page += 1
            print(f"Next page: {current_page}")
    
    elif touch.was_swiped(direction='right'):
        if current_page > 1:
            current_page -= 1
            print(f"Previous page: {current_page}")
    
    elif touch.was_touched():
        print(f"Tapped on page {current_page}")
```

### Touch Counter Game

```python
from easy_touch import Touch
from easy_display import Display
from time import sleep

touch = Touch()
display = Display()

score = 0
game_time = 10  # 10 seconds

display.clear()
display.show_text("Tap as fast as you can!\nGame starts in 3...")
sleep(3)

display.clear()
display.show_text("GO!")

start_time = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start_time) < (game_time * 1000):
    # Count all taps
    taps = touch.get_touches()
    score += taps
    
    if taps > 0:
        display.clear()
        display.show_text(f"Score: {score}")

display.clear()
display.show_text(f"Final Score: {score}\nTaps per second: {score/game_time:.1f}")
```

## Understanding Touch Coordinates

The touchscreen uses a coordinate system where:

- **X coordinates**: 0 (left edge) to 319 (right edge)
- **Y coordinates**: 0 (top edge) to 239 (bottom edge)
- **Origin (0,0)**: Top-left corner of the screen

```
(0,0) -----------------> (319,0)
  |                         |
  |                         |
  |        Screen           |
  |                         |
  |                         |
(0,239) ----------------> (319,239)
```

## Troubleshooting

**Touch coordinates seem wrong?**

- Run `touch.force_calibration()` to recalibrate
- Make sure you're touching the exact center of calibration crosshairs
- Check that your finger isn't too big or small for accurate detection

**Swipes not detected?**

- Swipes need to be at least 30 pixels long to be detected
- Make sure you're swiping in a reasonably straight line
- Try swiping faster and more deliberately

**Multiple touches detected for single tap?**

- Use `touch.clear_touch_history()` between different UI screens
- The touchscreen is resistive - avoid resting anything on it
- My fat finger tips weren't the best and would often register multiple taps - use a stylus!

**Touch seems unresponsive?**

- Check that your finger is making good contact with the screen
- Clean the screen surface if it's dirty or greasy
- Resistive touchscreens work best with firm, deliberate touches
