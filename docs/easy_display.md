# Easy Display Library

The Easy Display library makes it simple to show text, draw shapes, and create basic graphics on the ESP32-CYD's color display. It's designed to be easy for students and teachers to use without worrying about complex display details.

## Quick Start

```python
from easy_display import Display

# Create a display
display = Display()

# Show some text
display.show_text("Hello World!")

# Draw a circle
display.draw_circle(160, 120, 50, color="red")
```

## Basic Setup

```python
from easy_display import Display

# Create a display (uses the entire 320x240 screen)
display = Display()

# The display automatically clears to black when created
```

The display works in **landscape mode** with:
- **Width**: 320 pixels (left to right)
- **Height**: 240 pixels (top to bottom)
- **Colors**: Support for many colors (see color section below)

## Showing Text

### Simple Text Display

```python
# Show text starting from the top-left corner
display.show_text("This is my message")

# Text automatically wraps if it's too long for one line
display.show_text("This is a very long message that will automatically wrap to the next line when it gets too long")

# Show multiple lines of text
display.show_text("Line 1\nLine 2\nLine 3")

# Show text in different colors
display.show_text("Red text", color="red")
display.show_text("Blue text on yellow background", color="blue", background="yellow")
```

### Precise Text Positioning

```python
# Show text at exact coordinates (x, y)
display.show_text_at(10, 50, "Text at position 10, 50")
display.show_text_at(100, 100, "Centered text", color="green")

# Coordinates start at (0, 0) in the top-left corner
# x increases going right, y increases going down
```

## Drawing Shapes

### Basic Shapes

```python
# Draw a single dot
display.draw_pixel(160, 120, color="white")

# Draw lines
display.draw_line(0, 0, 319, 239, color="red")     # Diagonal line across screen
display.draw_line(50, 50, 100, 50, color="blue")   # Horizontal line

# Draw rectangles
display.draw_rectangle(50, 50, 100, 80, color="green")           # Outline only
display.draw_rectangle(200, 50, 100, 80, color="red", filled=True)  # Filled rectangle

# Draw circles
display.draw_circle(160, 120, 30, color="yellow")               # Outline only
display.draw_circle(80, 60, 25, color="purple", filled=True)    # Filled circle
```

### Advanced Shapes

```python
# Draw ellipses (oval shapes)
display.draw_ellipse(160, 120, 80, 40, color="cyan")            # Outline only
display.draw_ellipse(160, 120, 60, 100, color="orange", filled=True)  # Filled ellipse

# Draw polygons (connect multiple points)
triangle_points = [(160, 50), (100, 150), (220, 150)]  # Three points make a triangle
display.draw_polygon(triangle_points, color="magenta")

star_points = [(160, 40), (180, 100), (240, 100), (200, 140), (220, 200), (160, 170), (100, 200), (120, 140), (80, 100), (140, 100)]
display.draw_polygon(star_points, color="yellow", filled=True)
```

## Colors

You can use color names (strings) or RGB values:

### Color Names

```python
# Basic colors
"black", "white", "red", "green", "blue"

# Extended colors  
"yellow", "cyan", "magenta", "orange", "purple", "pink", "brown", "gray"

# Example usage
display.show_text("Hello", color="red")
display.draw_circle(100, 100, 30, color="blue")
```

### Custom RGB Colors

```python
# Use RGB values (red, green, blue) from 0-255
custom_purple = (128, 0, 128)
display.draw_rectangle(50, 50, 100, 100, color=custom_purple)

# Bright green
bright_green = (0, 255, 0)
display.show_text("Bright text!", color=bright_green)
```

## Screen Control

```python
# Clear the entire screen
display.clear()                    # Clear to black
display.clear(color="blue")        # Clear to blue

# Turn display on/off (saves power)
display.display_off()              # Turn off display
display.display_on()               # Turn on display

# Put display to sleep (saves more power)
display.sleep(True)                # Enter sleep mode
display.sleep(False)               # Wake up from sleep
```

## Performance Tips

For drawing lots of shapes or pixels, you can use buffering to make it (a bit) faster:

```python
# Start buffering (collect drawing commands)
display.begin_drawing()

# Do lots of drawing operations
for i in range(100):
    display.draw_pixel(i, i, color="white")

# Finish buffering (send all commands at once)
display.end_drawing()
```

## Common Examples

### Digital Clock Display

```python
from easy_display import Display
from time import sleep

display = Display()

while True:
    # Clear screen and show current time
    display.clear()
    display.show_text_at(100, 100, "12:34:56", color="green")
    sleep(1)
```

### Simple Drawing Program

```python
from easy_display import Display
from easy_touch import Touch

display = Display()
touch = Touch()

display.clear()
display.show_text("Touch screen to draw!")

while True:
    current_touch = touch.is_touched()
    if current_touch:
        x, y = current_touch['x'], current_touch['y']
        display.draw_pixel(x, y, color="white")
```

### Status Display

```python
from easy_display import Display

display = Display()

# Create a status display
display.clear()
display.show_text_at(10, 10, "System Status", color="cyan")
display.draw_line(10, 30, 310, 30, color="white")

display.show_text_at(10, 50, "Temperature: 23.5°C", color="green")
display.show_text_at(10, 70, "Humidity: 65%", color="blue")
display.show_text_at(10, 90, "Battery: 85%", color="yellow")

# Draw battery indicator
display.draw_rectangle(250, 85, 60, 20, color="white")
display.fill_rectangle(252, 87, 50, 16, color="green")  # 85% full
```

## Troubleshooting

**Text not showing up?**
- Check if coordinates are within screen bounds (0-319 for x, 0-239 for y)
- Make sure text color is different from background color
- Try `display.clear()` first to start with a clean screen

**Shapes appear cut off?**
- Check coordinates are within screen bounds
- Remember: x goes from 0 to 319, y goes from 0 to 239

**Display seems slow?**
- Use `begin_drawing()` and `end_drawing()` around multiple drawing operations
- Avoid clearing and redrawing the entire screen frequently
- Draw only the parts that need to change

**Nothing appears on screen?**
- Check if display is turned on with `display.display_on()`
- Make sure display isn't in sleep mode: `display.sleep(False)`

**Corrupted line of text?**
- Using the `show_text_at` method doesn't line wrap and so corrupts on long lines