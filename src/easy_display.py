"""
Easy Display Library for ESP32 with ILI9341 TFT Display
A student-friendly display library that hides all the complexity.

This library simplifies display operations for students by providing:
- Simple text display functions with automatic wrapping
- Basic shape drawing
- Easy color handling
- No complex setup required

Based on the ILI9341 library:
https://github.com/rdagger/micropython-ili9341

Example usage:
    from easy_display import Display

    # Create display
    display = Display()

    # Show text
    display.show_text("Hello World!")

    # Draw shapes
    display.draw_circle(160, 120, 50, color="red")
"""

from machine import Pin, SPI
from time import sleep as time_sleep
from framebuf import FrameBuffer, RGB565
from micropython import const


def color565(r, g, b):
    """Convert RGB values to 16-bit color format.

    Args:
        r (int): Red value (0-255)
        g (int): Green value (0-255)
        b (int): Blue value (0-255)

    Returns:
        int: 16-bit color value
    """
    return (b & 0xF8) << 8 | (g & 0xFC) << 3 | r >> 3


class Display:
    """Simple display interface for students."""

    # ILI9341 command constants (from original library)
    NOP = const(0x00)
    SWRESET = const(0x01)
    RDDID = const(0x04)
    RDDST = const(0x09)
    SLPIN = const(0x10)
    SLPOUT = const(0x11)
    PTLON = const(0x12)
    NORON = const(0x13)
    INVOFF = const(0x20)
    INVON = const(0x21)
    GAMMASET = const(0x26)
    DISPLAY_OFF = const(0x28)
    DISPLAY_ON = const(0x29)
    SET_COLUMN = const(0x2A)
    SET_PAGE = const(0x2B)
    WRITE_RAM = const(0x2C)
    READ_RAM = const(0x2E)
    PTLAR = const(0x30)
    VSCRDEF = const(0x33)
    MADCTL = const(0x36)
    VSCRSADD = const(0x37)
    PIXFMT = const(0x3A)
    FRMCTR1 = const(0xB1)
    DFUNCTR = const(0xB6)
    PWCTR1 = const(0xC0)
    PWCTR2 = const(0xC1)
    PWCTRA = const(0xCB)
    PWCTRB = const(0xCF)
    VMCTR1 = const(0xC5)
    VMCTR2 = const(0xC7)
    GMCTRP1 = const(0xE0)
    GMCTRN1 = const(0xE1)
    DTCA = const(0xE8)
    DTCB = const(0xEA)
    POSC = const(0xED)
    ENABLE3G = const(0xF2)
    PUMPRC = const(0xF7)

    # Color constants
    COLORS = {
        "black": color565(0, 0, 0),
        "white": color565(255, 255, 255),
        "red": color565(255, 0, 0),
        "green": color565(0, 255, 0),
        "blue": color565(0, 0, 255),
        "yellow": color565(255, 255, 0),
        "cyan": color565(0, 255, 255),
        "magenta": color565(255, 0, 255),
        "orange": color565(255, 165, 0),
        "purple": color565(128, 0, 128),
        "pink": color565(255, 192, 203),
        "brown": color565(165, 42, 42),
        "gray": color565(128, 128, 128),
        "grey": color565(128, 128, 128),
    }

    def __init__(self, width=320, height=240):
        """Initialize the display with default ESP32-2432S028R pinout.

        Args:
            width (int): Display width in pixels (default: 320)
            height (int): Display height in pixels (default: 240)
        """
        self.width = width
        self.height = height

        # Pixel buffer for performance optimization
        self._pixel_buffer = {}
        self._buffering_enabled = False

        # Default pin configuration for ESP32-2432S028R (CYD)
        self._setup_display()

        # Turn on backlight
        self._setup_backlight()

        # Clear screen to black
        self.clear()

    def _setup_display(self):
        """Set up the display hardware (internal use only)."""
        try:
            # Set up SPI for display (standard CYD pinout)
            self.spi = SPI(1, baudrate=60000000, sck=Pin(14), mosi=Pin(13))

            # Set up control pins
            self.cs = Pin(15, Pin.OUT, value=1)
            self.dc = Pin(2, Pin.OUT, value=0)
            self.rst = Pin(15, Pin.OUT, value=1)  # Reset shared with CS on CYD

            # Initialize display
            self._init_display()

        except ImportError as e:
            print(f"Display setup failed - missing module: {e}")
            print("This module requires MicroPython with machine module support")
            self._create_dummy_methods()
        except OSError as e:
            print(f"Display setup failed - hardware error: {e}")
            print("Check wiring and pin connections")
            self._create_dummy_methods()
        except Exception as e:
            print(f"Display setup failed - unexpected error: {e}")
            print(f"Error type: {type(e).__name__}")
            self._create_dummy_methods()

    def _setup_backlight(self):
        """Turn on the display backlight."""
        try:
            self.backlight = Pin(21, Pin.OUT)
            self.backlight.on()
        except Exception:
            pass  # Backlight pin might not be available

    def _init_display(self):
        """Initialize the ILI9341 display (based on original library)."""
        # Reset display
        self.rst.off()
        time_sleep(0.1)
        self.rst.on()
        time_sleep(0.1)

        # Send initialization commands
        self._write_cmd(self.SWRESET)
        time_sleep(0.1)
        self._write_cmd(self.PWCTRB, 0x00, 0xC1, 0x30)
        self._write_cmd(self.POSC, 0x64, 0x03, 0x12, 0x81)
        self._write_cmd(self.DTCA, 0x85, 0x00, 0x78)
        self._write_cmd(self.PWCTRA, 0x39, 0x2C, 0x00, 0x34, 0x02)
        self._write_cmd(self.PUMPRC, 0x20)
        self._write_cmd(self.DTCB, 0x00, 0x00)
        self._write_cmd(self.PWCTR1, 0x23)
        self._write_cmd(self.PWCTR2, 0x10)
        self._write_cmd(self.VMCTR1, 0x3E, 0x28)
        self._write_cmd(self.VMCTR2, 0x86)
        self._write_cmd(self.MADCTL, 0xE0)  # Landscape rotation
        self._write_cmd(self.VSCRSADD, 0x00)
        self._write_cmd(self.PIXFMT, 0x55)
        self._write_cmd(self.FRMCTR1, 0x00, 0x18)
        self._write_cmd(self.DFUNCTR, 0x08, 0x82, 0x27)
        self._write_cmd(self.ENABLE3G, 0x00)
        self._write_cmd(self.GAMMASET, 0x01)

        # Gamma correction (simplified)
        self._write_cmd(
            self.GMCTRP1,
            0x0F,
            0x31,
            0x2B,
            0x0C,
            0x0E,
            0x08,
            0x4E,
            0xF1,
            0x37,
            0x07,
            0x10,
            0x03,
            0x0E,
            0x09,
            0x00,
        )
        self._write_cmd(
            self.GMCTRN1,
            0x00,
            0x0E,
            0x14,
            0x03,
            0x11,
            0x07,
            0x31,
            0xC1,
            0x48,
            0x08,
            0x0F,
            0x0C,
            0x31,
            0x36,
            0x0F,
        )

        self._write_cmd(self.SLPOUT)
        time_sleep(0.1)
        self._write_cmd(self.DISPLAY_ON)
        time_sleep(0.1)

    def _write_cmd(self, command, *args):
        """Write command to display."""
        self.cs.off()
        self.dc.off()  # Command mode
        self.spi.write(bytearray([command]))
        if args:
            self.dc.on()  # Data mode
            self.spi.write(bytearray(args))
        self.cs.on()

    def _write_data(self, data):
        """Write data to display."""
        self.cs.off()
        self.dc.on()  # Data mode
        self.spi.write(data)
        self.cs.on()

    def _block(self, x0, y0, x1, y1, data):
        """Write a block of data to display."""
        self._write_cmd(self.SET_COLUMN, x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF)
        self._write_cmd(self.SET_PAGE, y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF)
        self._write_cmd(self.WRITE_RAM)
        self._write_data(data)

    def _create_dummy_methods(self):
        """Create dummy methods if display init fails."""

        def dummy(*args, **kwargs):
            pass

        self._write_cmd = dummy
        self._write_data = dummy
        self._block = dummy

    def _parse_color(self, color):
        """Convert color string or RGB values to 16-bit color.

        Args:
            color: Can be:
                - String: "red", "blue", etc.
                - Tuple: (r, g, b) values 0-255
                - Int: 16-bit color value

        Returns:
            int: 16-bit color value
        """
        if isinstance(color, str):
            color = color.lower()
            if color in self.COLORS:
                return self.COLORS[color]
            else:
                return self.COLORS["white"]  # Default to white for unknown colors
        elif isinstance(color, (list, tuple)) and len(color) >= 3:
            return color565(color[0], color[1], color[2])
        elif isinstance(color, int):
            return color
        else:
            return self.COLORS["white"]  # Default to white

    MAX_BUFFERED_PIXELS = 500  # Safety limit

    def _start_buffering(self):
        """Start buffering pixel operations for performance."""
        self._pixel_buffer.clear()
        self._buffering_enabled = True

    def _buffered_pixel(self, x, y, color):
        """Add a pixel to the buffer or draw immediately."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        color_val = self._parse_color(color)

        if self._buffering_enabled:
            # Safety check: prevent memory exhaustion
            if len(self._pixel_buffer) >= self.MAX_BUFFERED_PIXELS:
                # Flush current buffer and continue
                self._flush_buffer()
                self._start_buffering()

            self._pixel_buffer[(x, y)] = color_val
        else:
            pixel_data = color_val.to_bytes(2, "big")
            self._block(x, y, x, y, pixel_data)

    def _flush_buffer(self):
        """Flush all buffered pixels to the display with optimized SPI batching."""
        if not self._pixel_buffer:
            return

        # Group consecutive pixels by row for efficient SPI transfers
        rows = {}
        for (x, y), color in self._pixel_buffer.items():
            if y not in rows:
                rows[y] = []
            rows[y].append((x, color))

        # Prepare all block operations for batched execution
        block_operations = []

        for y, pixels in rows.items():
            pixels.sort()  # Sort by x coordinate

            # Group consecutive pixels into blocks
            i = 0
            while i < len(pixels):
                start_x = pixels[i][0]
                start_color = pixels[i][1]
                end_x = start_x

                # Find consecutive pixels with same color
                j = i + 1
                while (
                    j < len(pixels)
                    and pixels[j][0] == end_x + 1
                    and pixels[j][1] == start_color
                ):
                    end_x = pixels[j][0]
                    j += 1

                # Prepare block operation
                if start_x == end_x:
                    # Single pixel
                    pixel_data = start_color.to_bytes(2, "big")
                    block_operations.append((start_x, y, start_x, y, pixel_data))
                else:
                    # Multiple consecutive pixels
                    width = end_x - start_x + 1
                    line_data = start_color.to_bytes(2, "big") * width
                    block_operations.append((start_x, y, end_x, y, line_data))

                i = j

        # Execute all block operations with minimal GPIO overhead
        self._execute_block_batch(block_operations)

        self._pixel_buffer.clear()
        self._buffering_enabled = False

    def _execute_block_batch(self, block_operations):
        """Execute multiple block operations with optimized SPI batching.

        This method minimizes GPIO overhead by keeping CS low for the entire
        batch of operations, only toggling DC as needed.
        """
        if not block_operations:
            return

        # Start SPI transaction - keep CS low for entire batch
        self.cs.off()

        try:
            for x0, y0, x1, y1, data in block_operations:
                # Send SET_COLUMN command
                self.dc.off()  # Command mode
                self.spi.write(bytearray([self.SET_COLUMN]))
                self.dc.on()  # Data mode
                self.spi.write(bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))

                # Send SET_PAGE command
                self.dc.off()  # Command mode
                self.spi.write(bytearray([self.SET_PAGE]))
                self.dc.on()  # Data mode
                self.spi.write(bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))

                # Send WRITE_RAM command
                self.dc.off()  # Command mode
                self.spi.write(bytearray([self.WRITE_RAM]))

                # Send pixel data
                self.dc.on()  # Data mode
                self.spi.write(data)

        finally:
            # Always end SPI transaction
            self.cs.on()


    def clear(self, color="black"):
        """Clear the entire display.

        Args:
            color: Background color (default: "black")
        """
        color_val = self._parse_color(color)

        # Clear in chunks to avoid memory issues
        chunk_height = 8
        line_data = color_val.to_bytes(2, "big") * (self.width * chunk_height)

        for y in range(0, self.height, chunk_height):
            self._block(0, y, self.width - 1, y + chunk_height - 1, line_data)

    def show_text(self, text, color="white", background="black"):
        """Display text on screen with automatic wrapping.

        Args:
            text: String or list of strings to display
            color: Text color (default: "white")
            background: Background color (default: "black")
        """
        text_color = self._parse_color(color)
        bg_color = self._parse_color(background)

        # Clear screen first
        self.clear(background)

        # Handle both single strings and lists
        if isinstance(text, str):
            lines = text.split("\n")  # Split on newlines first
            # Then wrap long lines
            wrapped_lines = []
            for line in lines:
                wrapped_lines.extend(self._wrap_text(line))
            lines = wrapped_lines
        elif isinstance(text, (list, tuple)):
            lines = []
            for item in text:
                item_str = str(item)
                item_lines = item_str.split("\n")
                for line in item_lines:
                    lines.extend(self._wrap_text(line))
        else:
            lines = [str(text)]

        # Display lines
        y = 5  # Start position
        line_height = 11  # 8 pixels + 3 padding

        for line in lines:
            if y + 8 > self.height:  # Don't draw beyond screen
                break
            self._draw_text_8x8(5, y, line, text_color, bg_color)
            y += line_height

    def show_text_at(self, x, y, text, color="white", background="black"):
        """Display text at specific coordinates (no wrapping).

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            text: Text to display
            color: Text color (default: "white")
            background: Background color (default: "black")
        """
        text_color = self._parse_color(color)
        bg_color = self._parse_color(background)
        self._draw_text_8x8(x, y, str(text), text_color, bg_color)

    def _wrap_text(self, text, chars_per_line=40):
        """Wrap text to fit on screen."""
        if len(text) <= chars_per_line:
            return [text]

        lines = []
        words = text.split(" ")
        current_words = []
        current_length = 0

        for word in words:
            word_length = len(word)
            needed_length = current_length + word_length + (1 if current_words else 0)
            
            if needed_length <= chars_per_line:
                current_words.append(word)
                current_length = needed_length
            else:
                if current_words:
                    lines.append(" ".join(current_words))
                current_words = [word]
                current_length = word_length

        if current_words:
            lines.append(" ".join(current_words))

        return lines

    def _draw_text_8x8(self, x, y, text, color, background=0):
        """Draw text using 8x8 font (from original library)."""
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return

        w = len(text) * 8
        h = 8

        # Create framebuffer for text
        buf = bytearray(w * 16)  # 16 bits per pixel
        fbuf = FrameBuffer(buf, w, h, RGB565)

        if background != 0:
            # Swap bytes for framebuffer endianness
            b_color = ((background & 0xFF) << 8) | ((background & 0xFF00) >> 8)
            fbuf.fill(b_color)

        # Swap bytes for framebuffer endianness
        t_color = ((color & 0xFF) << 8) | ((color & 0xFF00) >> 8)
        fbuf.text(text, 0, 0, t_color)

        # Draw to display
        self._block(x, y, x + w - 1, y + h - 1, buf)

    def draw_pixel(self, x, y, color="white"):
        """Draw a single pixel.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            color: Pixel color (default: "white")
        """
        self._buffered_pixel(x, y, color)

    def draw_line(self, x1, y1, x2, y2, color="white"):
        """Draw a line between two points.

        Args:
            x1, y1 (int): Start coordinates
            x2, y2 (int): End coordinates
            color: Line color (default: "white")
        """
        # Use buffering for better performance
        self._start_buffering()

        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        x_inc = 1 if x1 < x2 else -1
        y_inc = 1 if y1 < y2 else -1
        error = dx - dy

        while True:
            self._buffered_pixel(x, y, color)
            if x == x2 and y == y2:
                break
            e2 = 2 * error
            if e2 > -dy:
                error -= dy
                x += x_inc
            if e2 < dx:
                error += dx
                y += y_inc

        self._flush_buffer()

    def draw_rectangle(self, x, y, width, height, color="white", filled=False):
        """Draw a rectangle.

        Args:
            x, y (int): Top-left corner coordinates
            width, height (int): Rectangle dimensions
            color: Rectangle color (default: "white")
            filled (bool): Whether to fill the rectangle (default: False)
        """
        # Input validation
        if width <= 0 or height <= 0:
            raise ValueError("Rectangle width and height must be positive")
            
        if filled:
            self.fill_rectangle(x, y, width, height, color)
        else:
            # Draw outline efficiently using direct lines
            color_val = self._parse_color(color)

            # Clip to screen bounds
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(self.width - 1, x + width - 1)
            y2 = min(self.height - 1, y + height - 1)

            if x1 <= x2 and y1 <= y2:
                line_data_h = color_val.to_bytes(2, "big") * (x2 - x1 + 1)
                line_data_v = color_val.to_bytes(2, "big")

                # Top and bottom lines
                if y >= 0 and y < self.height:
                    self._block(x1, y1, x2, y1, line_data_h)  # Top
                if y + height - 1 < self.height and y + height - 1 != y1:
                    self._block(x1, y2, x2, y2, line_data_h)  # Bottom

                # Left and right lines (excluding corners already drawn)
                for row in range(y1 + 1, y2):
                    if x >= 0 and x < self.width:
                        self._block(x1, row, x1, row, line_data_v)  # Left
                    if x + width - 1 < self.width and x + width - 1 != x1:
                        self._block(x2, row, x2, row, line_data_v)  # Right

    def fill_rectangle(self, x, y, width, height, color="white"):
        """Draw a filled rectangle.

        Args:
            x, y (int): Top-left corner coordinates
            width, height (int): Rectangle dimensions
            color: Fill color (default: "white")
        """
        color_val = self._parse_color(color)

        # Clip to screen bounds
        if x < 0:
            width += x
            x = 0
        if y < 0:
            height += y
            y = 0
        if x + width > self.width:
            width = self.width - x
        if y + height > self.height:
            height = self.height - y

        if width > 0 and height > 0:
            # Create line data
            line_data = color_val.to_bytes(2, "big") * width
            # Draw each line
            for row in range(height):
                self._block(x, y + row, x + width - 1, y + row, line_data)

    def draw_circle(self, x, y, radius, color="white", filled=False):
        """Draw a circle.

        Args:
            x, y (int): Center coordinates
            radius (int): Circle radius
            color: Circle color (default: "white")
            filled (bool): Whether to fill the circle (default: False)
        """
        if filled:
            self.fill_circle(x, y, radius, color)
        else:
            # Use buffering for better performance
            self._start_buffering()

            # Bresenham's circle algorithm
            f = 1 - radius
            dx = 1
            dy = -radius - radius
            px = 0
            py = radius

            self._buffered_pixel(x, y + radius, color)
            self._buffered_pixel(x, y - radius, color)
            self._buffered_pixel(x + radius, y, color)
            self._buffered_pixel(x - radius, y, color)

            while px < py:
                if f >= 0:
                    py -= 1
                    dy += 2
                    f += dy
                px += 1
                dx += 2
                f += dx

                self._buffered_pixel(x + px, y + py, color)
                self._buffered_pixel(x - px, y + py, color)
                self._buffered_pixel(x + px, y - py, color)
                self._buffered_pixel(x - px, y - py, color)
                self._buffered_pixel(x + py, y + px, color)
                self._buffered_pixel(x - py, y + px, color)
                self._buffered_pixel(x + py, y - px, color)
                self._buffered_pixel(x - py, y - px, color)

            self._flush_buffer()

    def fill_circle(self, x, y, radius, color="white"):
        """Draw a filled circle.

        Args:
            x, y (int): Center coordinates
            radius (int): Circle radius
            color: Fill color (default: "white")
        """
        color_val = self._parse_color(color)

        # Use scanline algorithm for efficiency - draw horizontal lines
        for dy in range(-radius, radius + 1):
            # Calculate half-width of circle at this y position
            half_width = int((radius * radius - dy * dy) ** 0.5)

            if half_width > 0:
                # Draw horizontal line across the circle
                start_x = max(0, x - half_width)
                end_x = min(self.width - 1, x + half_width)
                current_y = y + dy

                if 0 <= current_y < self.height and start_x <= end_x:
                    width = end_x - start_x + 1
                    line_data = color_val.to_bytes(2, "big") * width
                    self._block(start_x, current_y, end_x, current_y, line_data)

    def _draw_ellipse_points(self, cx, cy, x, y, color_val):
        """Helper method to draw the 4 symmetric points of an ellipse."""
        pixel_data = color_val.to_bytes(2, "big")
        
        # Draw 4 symmetric points
        if cx + x < self.width and cy + y < self.height and cx + x >= 0 and cy + y >= 0:
            self._block(cx + x, cy + y, cx + x, cy + y, pixel_data)
        if cx - x < self.width and cy + y < self.height and cx - x >= 0 and cy + y >= 0:
            self._block(cx - x, cy + y, cx - x, cy + y, pixel_data)
        if cx + x < self.width and cy - y < self.height and cx + x >= 0 and cy - y >= 0:
            self._block(cx + x, cy - y, cx + x, cy - y, pixel_data)
        if cx - x < self.width and cy - y < self.height and cx - x >= 0 and cy - y >= 0:
            self._block(cx - x, cy - y, cx - x, cy - y, pixel_data)

    def draw_ellipse(self, x, y, width, height, color="white", filled=False):
        """Draw an ellipse.

        Args:
            x, y (int): Center coordinates  
            width (int): Ellipse width (horizontal diameter)
            height (int): Ellipse height (vertical diameter)
            color: Ellipse color (default: "white")
            filled (bool): Whether to fill the ellipse (default: False)
        """
        if filled:
            self.fill_ellipse(x, y, width, height, color)
            return

        # Convert to semi-axes
        a = width // 2  # Semi-axis horizontal
        b = height // 2  # Semi-axis vertical
        
        if a <= 0 or b <= 0:
            return

        color_val = self._parse_color(color)
        
        # Bresenham ellipse algorithm
        a2 = a * a
        b2 = b * b
        twoa2 = 2 * a2
        twob2 = 2 * b2
        
        # Region 1
        px = 0
        py = twoa2 * b
        
        # Plot initial points
        self._draw_ellipse_points(x, y, 0, b, color_val)
        
        # Region 1 - horizontal direction
        p = round(b2 - (a2 * b) + (0.25 * a2))
        dx = 0
        dy = b
        
        while px < py:
            dx += 1
            px += twob2
            if p < 0:
                p += b2 + px
            else:
                dy -= 1
                py -= twoa2
                p += b2 + px - py
            self._draw_ellipse_points(x, y, dx, dy, color_val)
            
        # Region 2 - vertical direction  
        p = round(b2 * (dx + 0.5) * (dx + 0.5) + a2 * (dy - 1) * (dy - 1) - a2 * b2)
        
        while dy > 0:
            dy -= 1
            py -= twoa2
            if p > 0:
                p += a2 - py
            else:
                dx += 1
                px += twob2
                p += a2 - py + px
            self._draw_ellipse_points(x, y, dx, dy, color_val)

    def fill_ellipse(self, x, y, width, height, color="white"):
        """Draw a filled ellipse.

        Args:
            x, y (int): Center coordinates
            width (int): Ellipse width (horizontal diameter)  
            height (int): Ellipse height (vertical diameter)
            color: Fill color (default: "white")
        """
        # Convert to semi-axes
        a = width // 2
        b = height // 2
        
        if a <= 0 or b <= 0:
            return

        color_val = self._parse_color(color)

        # Use scanline algorithm for efficiency
        for dy in range(-b, b + 1):
            # Calculate half-width of ellipse at this y position
            if b == 0:
                half_width = 0
            else:
                # Ellipse equation: (x/a)² + (y/b)² = 1
                # Solve for x: x = a * sqrt(1 - (y/b)²)
                y_ratio = dy / b
                if abs(y_ratio) <= 1:
                    half_width = int(a * (1 - y_ratio * y_ratio) ** 0.5)
                else:
                    half_width = 0

            if half_width > 0:
                start_x = max(0, x - half_width)
                end_x = min(self.width - 1, x + half_width)
                current_y = y + dy

                if 0 <= current_y < self.height and start_x <= end_x:
                    line_width = end_x - start_x + 1
                    line_data = color_val.to_bytes(2, "big") * line_width
                    self._block(start_x, current_y, end_x, current_y, line_data)

    def draw_polygon(self, points, color="white", filled=False):
        """Draw a polygon from a list of points.

        Args:
            points (list): List of (x, y) coordinate tuples
            color: Polygon color (default: "white") 
            filled (bool): Whether to fill the polygon (default: False)
        """
        if len(points) < 3:
            return  # Need at least 3 points for a polygon

        if filled:
            self.fill_polygon(points, color)
        else:
            # Draw outline by connecting consecutive points
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]  # Wrap to first point
                self.draw_line(x1, y1, x2, y2, color)

    def fill_polygon(self, points, color="white"):
        """Draw a filled polygon using scanline algorithm.

        Args:
            points (list): List of (x, y) coordinate tuples
            color: Fill color (default: "white")
        """
        if len(points) < 3:
            return

        color_val = self._parse_color(color)
        
        # Find bounding box
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        # Clip to screen bounds
        min_y = max(0, min_y)
        max_y = min(self.height - 1, max_y)
        
        # For each scanline
        for y in range(min_y, max_y + 1):
            intersections = []
            
            # Find intersections with polygon edges
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                
                # Skip horizontal edges
                if y1 == y2:
                    continue
                    
                # Check if scanline intersects this edge
                if (y1 <= y < y2) or (y2 <= y < y1):
                    # Calculate intersection x coordinate
                    if y2 != y1:  # Avoid division by zero
                        x_intersect = x1 + (y - y1) * (x2 - x1) // (y2 - y1)
                        intersections.append(x_intersect)
            
            # Sort intersections and fill between pairs
            intersections.sort()
            for i in range(0, len(intersections), 2):
                if i + 1 < len(intersections):
                    start_x = max(0, intersections[i])
                    end_x = min(self.width - 1, intersections[i + 1])
                    
                    if start_x <= end_x:
                        line_width = end_x - start_x + 1
                        line_data = color_val.to_bytes(2, "big") * line_width
                        self._block(start_x, y, end_x, y, line_data)

    def display_on(self):
        """Turn the display on."""
        if hasattr(self, 'spi'):
            self._write_cmd(self.DISPLAY_ON)

    def display_off(self):
        """Turn the display off.""" 
        if hasattr(self, 'spi'):
            self._write_cmd(self.DISPLAY_OFF)

    def sleep(self, enable=True):
        """Enter or exit sleep mode.
        
        Args:
            enable (bool): True to enter sleep, False to exit (default: True)
        """
        if hasattr(self, 'spi'):
            if enable:
                self._write_cmd(self.SLPIN)
            else:
                self._write_cmd(self.SLPOUT)

    def begin_drawing(self):
        """Begin a buffered drawing operation for better performance.

        Use this when drawing multiple shapes to reduce SPI overhead.
        Must be paired with end_drawing().

        Example:
            display.begin_drawing()
            display.draw_pixel(10, 10, "red")
            display.draw_pixel(11, 10, "red")
            display.end_drawing()
        """
        self._start_buffering()

    def end_drawing(self):
        """End a buffered drawing operation and flush to display."""
        self._flush_buffer()


# Convenience functions for even simpler usage
_default_display = None


def init():
    """Initialize the default display instance."""
    global _default_display
    _default_display = Display()


def show_text(text, color="white", background="black"):
    """Show text using the default display.

    Args:
        text: Text to display
        color: Text color (default: "white")
        background: Background color (default: "black")
    """
    if _default_display is None:
        init()
    _default_display.show_text(text, color, background)


def show_text_at(x, y, text, color="white", background="black"):
    """Show text at position using the default display.

    Args:
        x, y (int): Position
        text: Text to display
        color: Text color (default: "white")
        background: Background color (default: "black")
    """
    if _default_display is None:
        init()
    _default_display.show_text_at(x, y, text, color, background)


def clear(color="black"):
    """Clear the default display.

    Args:
        color: Background color (default: "black")
    """
    if _default_display is None:
        init()
    _default_display.clear(color)


def draw_circle(x, y, radius, color="white", filled=False):
    """Draw a circle using the default display.

    Args:
        x, y (int): Center coordinates
        radius (int): Circle radius
        color: Circle color (default: "white")
        filled (bool): Whether to fill (default: False)
    """
    if _default_display is None:
        init()
    _default_display.draw_circle(x, y, radius, color, filled)


def draw_rectangle(x, y, width, height, color="white", filled=False):
    """Draw a rectangle using the default display.

    Args:
        x, y (int): Top-left coordinates
        width, height (int): Dimensions
        color: Rectangle color (default: "white")
        filled (bool): Whether to fill (default: False)
    """
    if _default_display is None:
        init()
    _default_display.draw_rectangle(x, y, width, height, color, filled)


def begin_drawing():
    """Begin buffered drawing for better performance."""
    if _default_display is None:
        init()
    _default_display.begin_drawing()


def end_drawing():
    """End buffered drawing and flush to display."""
    if _default_display is None:
        init()
    _default_display.end_drawing()


def draw_pixel(x, y, color="white"):
    """Draw a pixel using the default display.
    
    Args:
        x, y (int): Coordinates
        color: Pixel color (default: "white")
    """
    if _default_display is None:
        init()
    _default_display.draw_pixel(x, y, color)


def draw_line(x1, y1, x2, y2, color="white"):
    """Draw a line using the default display.
    
    Args:
        x1, y1 (int): Start coordinates
        x2, y2 (int): End coordinates
        color: Line color (default: "white")
    """
    if _default_display is None:
        init()
    _default_display.draw_line(x1, y1, x2, y2, color)


def draw_ellipse(x, y, width, height, color="white", filled=False):
    """Draw an ellipse using the default display.
    
    Args:
        x, y (int): Center coordinates
        width (int): Ellipse width (horizontal diameter)
        height (int): Ellipse height (vertical diameter)
        color: Ellipse color (default: "white")
        filled (bool): Whether to fill the ellipse (default: False)
    """
    if _default_display is None:
        init()
    _default_display.draw_ellipse(x, y, width, height, color, filled)


def draw_polygon(points, color="white", filled=False):
    """Draw a polygon using the default display.
    
    Args:
        points (list): List of (x, y) coordinate tuples
        color: Polygon color (default: "white")
        filled (bool): Whether to fill the polygon (default: False)
    """
    if _default_display is None:
        init()
    _default_display.draw_polygon(points, color, filled)


def display_on():
    """Turn display on using the default display."""
    if _default_display is None:
        init()
    _default_display.display_on()


def display_off():
    """Turn display off using the default display."""
    if _default_display is None:
        init()
    _default_display.display_off()


def display_sleep(enable=True):
    """Enter/exit sleep mode using the default display.
    
    Args:
        enable (bool): True to enter sleep, False to exit (default: True)
    """
    if _default_display is None:
        init()
    _default_display.sleep(enable)
