"""
Easy Touch Library for ESP32 with XPT2046 Touch Controller
A student-friendly touch interface library that hides all the complexity.

This library simplifies touch operations for students by providing:
- Simple touch detection functions
- Automatic calibration
- Easy callback setup
- No complex configuration required

Based on the XPT2046 library:
https://github.com/rdagger/micropython-ili9341

Example usage:
    from easy_touch import Touch
    
    # Create touch interface
    touch = Touch()
    
    # Check for touches
    pos = touch.get_touch()
    if pos:
        print(f"Touch at {pos['x']}, {pos['y']}")
    
    # Or use a callback function
    def on_touch(x, y):
        print(f"Touched at {x}, {y}")
    
    touch = Touch(on_touch=on_touch)
"""

from machine import Pin, SPI
from time import sleep
from micropython import const
import json

# Try to import display for auto-calibration
try:
    from easy_display import Display
    _display_available = True
except ImportError:
    _display_available = False


class Touch:
    """Simple touch interface for students."""
    
    # XPT2046 command constants (from original library)
    GET_X = const(0b11010000)
    GET_Y = const(0b10010000)
    GET_Z1 = const(0b10110000)
    GET_Z2 = const(0b11000000)
    GET_TEMP0 = const(0b10000000)
    GET_TEMP1 = const(0b11110000)
    GET_BATTERY = const(0b10100000)
    GET_AUX = const(0b11100000)
    
    def __init__(self, on_touch=None, width=320, height=240, flip_x=None, flip_y=None, swap_xy=None, auto_calibrate=True):
        """Initialize the touch interface with default ESP32-2432S028R pinout.
        
        Args:
            on_touch: Optional callback function to call when touched: on_touch(x, y)
            width (int): Display width in pixels (default: 320)
            height (int): Display height in pixels (default: 240)
            flip_x (bool): Flip X coordinates to match display (None = auto-detect)
            flip_y (bool): Flip Y coordinates to match display (None = auto-detect)
            swap_xy (bool): Swap X and Y coordinates for portrait/landscape mismatch (None = auto-detect)
            auto_calibrate (bool): Auto-calibrate if no saved calibration exists (default: True)
        """
        self.width = width
        self.height = height
        self.on_touch_callback = on_touch
        self.touch_count = 0
        
        # Load saved calibration or use defaults
        saved_config = self._load_calibration()
        
        # Set transform parameters (use saved values or provided values or defaults)
        self.flip_x = flip_x if flip_x is not None else saved_config.get('flip_x', True)
        self.flip_y = flip_y if flip_y is not None else saved_config.get('flip_y', True) 
        self.swap_xy = swap_xy if swap_xy is not None else saved_config.get('swap_xy', True)
        
        # Set calibration values (use saved values or defaults)
        self.x_min = saved_config.get('x_min', 100)
        self.x_max = saved_config.get('x_max', 1962)
        self.y_min = saved_config.get('y_min', 100)
        self.y_max = saved_config.get('y_max', 1900)
        
        # Calculate conversion factors
        self._recalculate_factors()
        
        # Set up touch hardware
        self._setup_touch()
        
        # Auto-calibrate if requested and no saved calibration exists
        if auto_calibrate and not saved_config.get('calibrated', False) and _display_available:
            print("Touch: No calibration found, starting auto-calibration...")
            self._auto_calibrate_with_display()
    
    def _load_calibration(self):
        """Load saved calibration from file."""
        try:
            with open('touch_calibration.json', 'r') as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}
    
    def _save_calibration(self):
        """Save current calibration to file."""
        calibration_data = {
            'x_min': self.x_min,
            'x_max': self.x_max,
            'y_min': self.y_min,
            'y_max': self.y_max,
            'flip_x': self.flip_x,
            'flip_y': self.flip_y,
            'swap_xy': self.swap_xy,
            'width': self.width,
            'height': self.height,
            'calibrated': True
        }
        try:
            with open('touch_calibration.json', 'w') as f:
                json.dump(calibration_data, f)
            print("Touch calibration saved successfully")
        except OSError as e:
            print(f"Failed to save calibration: {e}")
    
    def _recalculate_factors(self):
        """Recalculate conversion factors based on current calibration."""
        if self.swap_xy:
            # When coordinates are swapped:
            # Raw X range (129-1950) needs to map to screen Y dimension (0-239)
            # Raw Y range (64-1869) needs to map to screen X dimension (0-319)
            self.x_multiplier = self.width / (self.y_max - self.y_min)   # Screen X from Raw Y
            self.x_add = self.y_min * -self.x_multiplier
            self.y_multiplier = self.height / (self.x_max - self.x_min)  # Screen Y from Raw X
            self.y_add = self.x_min * -self.y_multiplier
        else:
            # Normal mapping - raw X to screen X, raw Y to screen Y
            self.x_multiplier = self.width / (self.x_max - self.x_min)
            self.x_add = self.x_min * -self.x_multiplier
            self.y_multiplier = self.height / (self.y_max - self.y_min)
            self.y_add = self.y_min * -self.y_multiplier

    def _auto_calibrate_with_display(self):
        """Auto-calibrate using display for visual guidance."""
        if not _display_available:
            print("Display not available for auto-calibration")
            return False
        
        print("Starting auto-calibration with display guidance...")
        
        # Create display instance for calibration
        cal_display = Display()
        cal_display.clear()
        
        # Test different transform configurations
        configs_to_test = [
            {"flip_x": True, "flip_y": True, "swap_xy": True, "name": "Flipped + Swapped"},
            {"flip_x": False, "flip_y": False, "swap_xy": True, "name": "Only Swapped"},
            {"flip_x": True, "flip_y": False, "swap_xy": True, "name": "X Flipped + Swapped"},
            {"flip_x": False, "flip_y": True, "swap_xy": True, "name": "Y Flipped + Swapped"},
            {"flip_x": True, "flip_y": True, "swap_xy": False, "name": "Both Flipped"},
            {"flip_x": False, "flip_y": False, "swap_xy": False, "name": "No Transform"},
        ]
        
        best_config = None
        best_score = float('inf')
        
        for config in configs_to_test:
            cal_display.clear()
            cal_display.show_text_at(10, 10, "Touch Calibration", "white")
            cal_display.show_text_at(10, 30, f"Testing: {config['name']}", "yellow")
            cal_display.show_text_at(10, 50, "Touch the RED targets:", "white")
            
            # Test this configuration
            self.flip_x = config["flip_x"]
            self.flip_y = config["flip_y"]
            self.swap_xy = config["swap_xy"]
            
            score = self._test_transform_accuracy(cal_display)
            
            if score < best_score:
                best_score = score
                best_config = config
            
            sleep(1)  # Brief pause between tests
        
        if best_config:
            # Apply best configuration
            self.flip_x = best_config["flip_x"]
            self.flip_y = best_config["flip_y"]
            self.swap_xy = best_config["swap_xy"]
            
            # Now do precise calibration with the best transform
            cal_points = self._calibrate_bounds_with_display(cal_display)
            
            if cal_points:
                # Apply new calibration bounds
                self.x_min = cal_points['x_min']
                self.x_max = cal_points['x_max']
                self.y_min = cal_points['y_min']
                self.y_max = cal_points['y_max']
                self._recalculate_factors()
                
                # Save the calibration
                self._save_calibration()
                
                # Show success message
                cal_display.clear()
                cal_display.show_text_at(50, 100, "Calibration Complete!", "green")
                cal_display.show_text_at(50, 120, f"Config: {best_config['name']}", "white")
                cal_display.show_text_at(50, 140, "Touch anywhere to continue", "gray")
                
                # Wait for touch to continue
                while not self._raw_touch():
                    sleep(0.1)
                
                cal_display.clear()
                return True
        
        cal_display.clear()
        cal_display.show_text_at(50, 100, "Calibration Failed", "red")
        cal_display.show_text_at(50, 120, "Using default settings", "white")
        sleep(2)
        cal_display.clear()
        return False
    
    def _test_transform_accuracy(self, display):
        """Test how accurate the current transform is by checking corner touches."""
        # Draw targets at the corners
        targets = [
            (20, 20, "top-left"),
            (300, 20, "top-right"),
            (20, 220, "bottom-left"),
            (300, 220, "bottom-right")
        ]
        
        total_error = 0
        successful_touches = 0
        
        for target_x, target_y, corner_name in targets:
            display.clear()
            display.show_text_at(10, 10, "Touch Calibration", "white")
            display.show_text_at(10, 30, "Touch the RED square", "white")
            display.show_text_at(10, 50, f"Corner: {corner_name}", "yellow")
            
            # Draw target square
            display.fill_rectangle(target_x-10, target_y-10, 20, 20, "red")
            display.draw_rectangle(target_x-10, target_y-10, 20, 20, "white")
            
            # Wait for touch and measure accuracy
            touch_detected = False
            timeout = 5.0  # 5 second timeout per target
            start_time = 0
            
            while start_time < timeout and not touch_detected:
                raw_pos = self._raw_touch()
                if raw_pos:
                    # Apply current transform to see where touch appears
                    screen_x, screen_y = self._normalize(*raw_pos)
                    
                    # Calculate error from target
                    error = ((screen_x - target_x)**2 + (screen_y - target_y)**2)**0.5
                    total_error += error
                    successful_touches += 1
                    touch_detected = True
                    
                    # Brief feedback
                    display.show_text_at(10, 200, f"Touch: ({screen_x}, {screen_y})", "green")
                    display.show_text_at(10, 215, f"Error: {error:.1f} pixels", "cyan")
                    sleep(1)
                
                sleep(0.1)
                start_time += 0.1
            
            if not touch_detected:
                total_error += 1000  # Heavy penalty for no touch
        
        # Return average error (lower is better)
        return total_error / max(1, successful_touches) if successful_touches > 0 else 1000
    
    def _calibrate_bounds_with_display(self, display):
        """Calibrate the raw coordinate bounds using display guidance."""
        display.clear()
        display.show_text_at(10, 10, "Precise Calibration", "white")
        display.show_text_at(10, 30, "Touch and hold targets", "white")
        display.show_text_at(10, 50, "for accurate bounds", "white")
        
        corners = [
            (5, 5, "top-left"),
            (315, 5, "top-right"),
            (5, 235, "bottom-left"),
            (315, 235, "bottom-right"),
            (160, 120, "center")
        ]
        
        raw_points = []
        
        for corner_x, corner_y, corner_name in corners:
            display.clear()
            display.show_text_at(10, 10, "Precise Calibration", "white")
            display.show_text_at(10, 30, f"Touch: {corner_name}", "yellow")
            display.show_text_at(10, 50, "Hold firmly for 2 seconds", "white")
            
            # Draw target
            display.fill_rectangle(corner_x-5, corner_y-5, 10, 10, "red")
            display.draw_rectangle(corner_x-5, corner_y-5, 10, 10, "white")
            
            # Collect samples
            samples = []
            sample_count = 0
            
            while sample_count < 15:  # 15 samples per corner
                raw_pos = self._raw_touch()
                if raw_pos:
                    samples.append(raw_pos)
                    sample_count += 1
                    display.show_text_at(10, 200, f"Sample {sample_count}/15", "green")
                sleep(0.1)
            
            if samples:
                # Calculate average
                avg_x = sum(s[0] for s in samples) // len(samples)
                avg_y = sum(s[1] for s in samples) // len(samples)
                raw_points.append((avg_x, avg_y))
                display.show_text_at(10, 215, f"Average: ({avg_x}, {avg_y})", "cyan")
            
            sleep(1)  # Pause between corners
        
        if len(raw_points) >= 4:
            # Calculate bounds with margin
            all_x = [p[0] for p in raw_points]
            all_y = [p[1] for p in raw_points]
            
            margin = 50
            return {
                'x_min': min(all_x) - margin,
                'x_max': max(all_x) + margin,
                'y_min': min(all_y) - margin,
                'y_max': max(all_y) + margin
            }
        
        return None
    
    def _setup_touch(self):
        """Set up the touch hardware (internal use only)."""
        try:
            # Set up SPI for touchscreen (standard CYD pinout)
            self.spi = SPI(2, baudrate=1000000, sck=Pin(25), mosi=Pin(32), miso=Pin(39))
            
            # Set up control pins
            self.cs = Pin(33, Pin.OUT, value=1)
            
            # Set up interrupt pin if callback is provided
            if self.on_touch_callback:
                self.int_pin = Pin(36, Pin.IN)
                self.int_locked = False
                self.int_pin.irq(trigger=self.int_pin.IRQ_FALLING | self.int_pin.IRQ_RISING,
                               handler=self._interrupt_handler)
            else:
                self.int_pin = None
            
            # Create buffers for SPI communication
            self.rx_buf = bytearray(3)
            self.tx_buf = bytearray(3)
            
        except Exception as e:
            print(f"Touch setup failed: {e}")
            # Create dummy methods so program doesn't crash
            self._create_dummy_methods()
    
    def _create_dummy_methods(self):
        """Create dummy methods if touch init fails."""
        def dummy(*args, **kwargs):
            return None
        self._send_command = dummy
        self._raw_touch = dummy
    
    def _send_command(self, command):
        """Send command to XPT2046 and get response."""
        try:
            self.tx_buf[0] = command
            self.cs.off()
            self.spi.write_readinto(self.tx_buf, self.rx_buf)
            self.cs.on()
            return (self.rx_buf[1] << 4) | (self.rx_buf[2] >> 4)
        except Exception:
            return 0
    
    def _raw_touch(self):
        """Read raw touch coordinates."""
        try:
            x = self._send_command(self.GET_X)
            y = self._send_command(self.GET_Y)
            
            # Check if coordinates are within expected range
            if self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max:
                return (x, y)
            else:
                return None
        except Exception:
            return None
    
    def _normalize(self, x, y):
        """Convert raw coordinates to screen coordinates."""
        # Apply the coordinate transformation
        if self.swap_xy:
            # When swapped: raw_y becomes screen_x, raw_x becomes screen_y
            screen_x = int(self.x_multiplier * y + self.x_add)  # Raw Y → Screen X
            screen_y = int(self.y_multiplier * x + self.y_add)  # Raw X → Screen Y
        else:
            # Normal mapping
            screen_x = int(self.x_multiplier * x + self.x_add)
            screen_y = int(self.y_multiplier * y + self.y_add)
    
        # Apply flipping after coordinate conversion
        if self.flip_x:
            screen_x = self.width - 1 - screen_x
        if self.flip_y:
            screen_y = self.height - 1 - screen_y
    
        # Clamp to screen bounds
        screen_x = max(0, min(screen_x, self.width - 1))
        screen_y = max(0, min(screen_y, self.height - 1))
    
        return screen_x, screen_y
    
    def _interrupt_handler(self, pin):
        """Handle touch interrupts (internal use only)."""
        if not pin.value() and not self.int_locked and self.on_touch_callback:
            self.int_locked = True
            
            # Get touch coordinates
            raw_pos = self._raw_touch()
            if raw_pos:
                x, y = self._normalize(*raw_pos)
                self.touch_count += 1
                
                # Call the user's callback function
                try:
                    self.on_touch_callback(x, y)
                except Exception as e:
                    print(f"Error in touch callback: {e}")
            
            sleep(0.1)  # Debounce
        elif pin.value() and self.int_locked:
            sleep(0.1)  # Debounce
            self.int_locked = False
    
    def get_touch(self):
        """Check for a touch and return coordinates.
        
        Returns:
            dict or None: Touch info with keys 'x', 'y', 'count' or None if no touch
        """
        # If using interrupts, this method is less useful, but still available
        if self.int_pin and self.on_touch_callback:
            # When using callbacks, just handle the interrupt
            return None
        
        # Take multiple samples for accuracy (from original library)
        timeout = 2  # 2 second timeout
        confidence = 5
        samples = [[0, 0] for _ in range(confidence)]
        sample_ptr = 0
        valid_samples = 0
        
        while timeout > 0:
            if valid_samples == confidence:
                # Calculate average
                avg_x = sum(s[0] for s in samples) // confidence
                avg_y = sum(s[1] for s in samples) // confidence
                
                # Check consistency (low deviation means good touch)
                deviation = sum((s[0] - avg_x)**2 + (s[1] - avg_y)**2 for s in samples) / confidence
                
                if deviation <= 50:  # Touch is stable
                    screen_x, screen_y = self._normalize(avg_x, avg_y)
                    self.touch_count += 1
                    return {
                        'x': screen_x,
                        'y': screen_y,
                        'count': self.touch_count
                    }
            
            # Get a new sample
            raw_pos = self._raw_touch()
            if raw_pos is None:
                valid_samples = 0  # Reset if no valid touch
            else:
                samples[sample_ptr] = raw_pos
                sample_ptr = (sample_ptr + 1) % confidence
                valid_samples = min(valid_samples + 1, confidence)
            
            sleep(0.05)
            timeout -= 0.05
        
        return None  # No valid touch detected
    
    def is_touched(self):
        """Simple check if screen is currently being touched.
        
        Returns:
            bool: True if screen is touched, False otherwise
        """
        return self._raw_touch() is not None
    
    def wait_for_touch(self, timeout=10):
        """Wait for a touch to occur.
        
        Args:
            timeout (float): Maximum time to wait in seconds (default: 10)
            
        Returns:
            dict or None: Touch info or None if timeout
        """
        start_time = 0
        while start_time < timeout:
            touch = self.get_touch()
            if touch:
                return touch
            sleep(0.1)
            start_time += 0.1
        return None
    
    def calibrate(self, x_min=None, x_max=None, y_min=None, y_max=None, save=True):
        """Calibrate touch coordinates (for advanced users).
        
        Args:
            x_min, x_max, y_min, y_max: Raw coordinate ranges
            save (bool): Save calibration to file (default: True)
        """
        if x_min is not None:
            self.x_min = x_min
        if x_max is not None:
            self.x_max = x_max
        if y_min is not None:
            self.y_min = y_min
        if y_max is not None:
            self.y_max = y_max
        
        # Recalculate conversion factors
        self._recalculate_factors()
        
        # Save calibration if requested
        if save:
            self._save_calibration()
    
    def recalibrate(self):
        """Force a recalibration using display guidance."""
        if _display_available:
            print("Starting manual recalibration...")
            return self._auto_calibrate_with_display()
        else:
            print("Display not available for calibration")
            print("Use manual calibration: touch.calibrate(x_min, x_max, y_min, y_max)")
            return False
    
    def reset_calibration(self):
        """Reset to default calibration and delete saved file."""
        try:
            import os
            os.remove('touch_calibration.json')
            print("Saved calibration deleted")
        except OSError:
            pass
        
        # Reset to defaults
        self.x_min = 100
        self.x_max = 1962
        self.y_min = 100
        self.y_max = 1900
        self.flip_x = True
        self.flip_y = True
        self.swap_xy = True
        self._recalculate_factors()
        print("Touch calibration reset to defaults")
    
    def set_coordinate_flipping(self, flip_x=None, flip_y=None, swap_xy=None):
        """Configure coordinate flipping and swapping to match display orientation.
        
        Args:
            flip_x (bool): If True, flip X coordinates (left becomes right)
            flip_y (bool): If True, flip Y coordinates (top becomes bottom)
            swap_xy (bool): If True, swap X and Y coordinates (portrait/landscape)
        """
        if flip_x is not None:
            self.flip_x = flip_x
        if flip_y is not None:
            self.flip_y = flip_y
        if swap_xy is not None:
            self.swap_xy = swap_xy
        
        print(f"Coordinate transform: X={self.flip_x}, Y={self.flip_y}, Swap={self.swap_xy}")
    
    def test_coordinates(self):
        """Test coordinate mapping by reporting touch positions.
        
        Touch the corners and edges to verify coordinate mapping is correct.
        """
        print("Touch Coordinate Test")
        print("Touch the corners and edges to verify mapping:")
        print("- Top-left should report coordinates near (0, 0)")
        print("- Top-right should report coordinates near ({}, 0)".format(self.width-1))
        print("- Bottom-left should report coordinates near (0, {})".format(self.height-1))
        print("- Bottom-right should report coordinates near ({}, {})".format(self.width-1, self.height-1))
        print("Press Ctrl+C to exit test")
        
        try:
            while True:
                touch = self.get_touch()
                if touch:
                    x, y = touch['x'], touch['y']
                    print(f"Touch at ({x}, {y})")
                sleep(0.1)
        except KeyboardInterrupt:
            print("\nCoordinate test finished")
    
    def get_stats(self):
        """Get touch statistics.
        
        Returns:
            dict: Statistics with 'touch_count' key
        """
        return {
            'touch_count': self.touch_count,
            'width': self.width,
            'height': self.height,
            'calibration': {
                'x_min': self.x_min,
                'x_max': self.x_max,
                'y_min': self.y_min,
                'y_max': self.y_max
            }
        }


# Convenience functions for even simpler usage
_default_touch = None

def init(on_touch=None, auto_calibrate=True):
    """Initialize the default touch instance with auto-calibration.
    
    Args:
        on_touch: Optional callback function: on_touch(x, y)
        auto_calibrate (bool): Auto-calibrate if no saved calibration exists (default: True)
    """
    global _default_touch
    _default_touch = Touch(on_touch=on_touch, auto_calibrate=auto_calibrate)

def get_touch():
    """Get touch using the default touch instance.
    
    Returns:
        dict or None: Touch info or None
    """
    if _default_touch is None:
        init()
    return _default_touch.get_touch()

def is_touched():
    """Check if screen is touched using default instance.
    
    Returns:
        bool: True if touched
    """
    if _default_touch is None:
        init()
    return _default_touch.is_touched()

def wait_for_touch(timeout=10):
    """Wait for touch using default instance.
    
    Args:
        timeout (float): Timeout in seconds
        
    Returns:
        dict or None: Touch info or None
    """
    if _default_touch is None:
        init()
    return _default_touch.wait_for_touch(timeout)

def stats():
    """Get touch statistics from default instance.
    
    Returns:
        dict: Statistics
    """
    if _default_touch is None:
        init()
    return _default_touch.get_stats()
