"""
Easy Touch Library v2 for ESP32 with XPT2046 Touch Controller
A student-friendly touch interface library with hardware timer-based detection.

This library provides:
- Hardware timer-based touch detection that runs automatically
- Automatic calibration system for touch accuracy with visual feedback using easy_display.py
- Clean, student-friendly API
- Event-based touch detection similar to micro:bit buttons

Example usage:
    from easy_touch import Touch
    from time import sleep
    
    # Create touch interface (timer starts automatically on touch)
    touch = Touch()
    
    while True:
        # Check for current touch
        current_touch = touch.is_touched()
        if current_touch:
            print(f"Currently touching at {current_touch['x']}, {current_touch['y']}")
        
        # Check for completed touches (taps)
        if touch.was_touched():
            coords = touch.get_last_touch_coords()
            print(f"Tapped at {coords}")
        
        # Count total taps since last check
        tap_count = touch.get_touches()
        if tap_count > 0:
            print(f"Total taps: {tap_count}")
        
        # Check for swipes
        if touch.was_swiped(direction='left'):
            print("Left swipe detected!")
        
        if touch.was_swiped(direction='right'):
            print("Right swipe detected!")
            
        if touch.was_swiped(direction='up'):
            print("Up swipe detected!")
            
        if touch.was_swiped(direction='down'):
            print("Down swipe detected!")
        
        # Check for any swipe in a specific area
        if touch.was_swiped(bounds=(5, 5, 100, 100)):
            print("Swipe in top-left area!")
        
        # Check for any swipe anywhere
        if touch.was_swiped():
            print("Some kind of swipe detected!")
        
        sleep(0.05)
"""

from machine import Pin, SPI, Timer
import micropython
from micropython import const
import json
from time import ticks_ms, ticks_diff, sleep

# Try to import display for auto-calibration
try:
    from easy_display import Display
    _display_available = True
except ImportError:
    _display_available = False

# XPT2046 command constants
GET_X = const(0b11010000)
GET_Y = const(0b10010000)
GET_Z1 = const(0b10110000)
GET_Z2 = const(0b11000000)

# Touch detection constants
MIN_SWIPE_DISTANCE = 30
MAX_TAP_DISTANCE = 8

# Allocate emergency exception buffer for interrupt handling
micropython.alloc_emergency_exception_buf(100)


class Touch:
    """Touch interface with hardware timer-based polling.
    This library uses hardware timers to poll touch positions only while
    a finger is touching the screen, providing efficient gesture detection.
    """
    
    def __init__(self, width=320, height=240, flip_x=None, flip_y=None, swap_xy=None, auto_calibrate=True):
        """Initialize the touch interface with default ESP32-2432S028R pinout.
        
        Args:
            width (int): Display width in pixels (default: 320)
            height (int): Display height in pixels (default: 240)
            flip_x (bool): Flip X coordinates to match display (None = auto-detect)
            flip_y (bool): Flip Y coordinates to match display (None = auto-detect)
            swap_xy (bool): Swap X and Y coordinates for portrait/landscape mismatch (None = auto-detect)
            auto_calibrate (bool): Auto-calibrate if no saved calibration exists (default: True)
        """
        self.width = width
        self.height = height
        
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
        
        # Event flags - set by interrupt handler, read by API methods
        self._was_touched = False
        self._was_swiped_up = False
        self._was_swiped_down = False
        self._was_swiped_left = False
        self._was_swiped_right = False
        self._last_touch_x = -1
        self._last_touch_y = -1
        self._current_touch_x = -1
        self._current_touch_y = -1
        self._is_currently_touched = False
        
        # Touch counter for get_touches() method (like micro:bit get_presses)
        self._touch_count = 0
        
        # Internal state for gesture tracking
        self._touch_down = False
        self._start_x = 0
        self._start_y = 0
        self._touch_positions = []  # Store all positions during touch
        self._last_irq_time = 0
        self._irq_debounce_ms = 20  # 20ms debounce
        
        # Hardware timer for polling touch positions
        self._timer = Timer(0)
        self._timer_active = False
        
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
        config = {
            'flip_x': self.flip_x,
            'flip_y': self.flip_y,
            'swap_xy': self.swap_xy,
            'x_min': self.x_min,
            'x_max': self.x_max,
            'y_min': self.y_min,
            'y_max': self.y_max,
            'calibrated': True
        }
        try:
            with open('touch_calibration.json', 'w') as f:
                json.dump(config, f)
        except OSError:
            print("Warning: Could not save touch calibration")
    
    def _recalculate_factors(self):
        """Recalculate coordinate conversion factors."""
        self._x_factor = self.width / (self.x_max - self.x_min)
        self._y_factor = self.height / (self.y_max - self.y_min)
    
    def _setup_touch(self):
        """Set up touch hardware (SPI and interrupt)."""
        # Set up SPI for XPT2046
        self.spi = SPI(2, baudrate=1000000, polarity=0, phase=0, 
                      sck=Pin(25), mosi=Pin(32), miso=Pin(39))
        
        # Set up CS pin
        self.cs = Pin(33, Pin.OUT, value=1)
        
        # Set up interrupt pin (Pin 36 for ESP32-2432S028R)
        self.irq_pin = Pin(36, Pin.IN)
        self.irq_pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, 
                        handler=self._touch_irq_handler)
    
    def _raw_touch(self):
        """Read raw touch coordinates from XPT2046."""
        try:
            # Pull CS low to start communication
            self.cs.value(0)
            
            # Read X coordinate
            x_bytes = bytearray(3)
            self.spi.write_readinto(bytes([GET_X, 0x00, 0x00]), x_bytes)
            x_raw = ((x_bytes[1] << 8) | x_bytes[2]) >> 3
            
            # Read Y coordinate
            y_bytes = bytearray(3)
            self.spi.write_readinto(bytes([GET_Y, 0x00, 0x00]), y_bytes)
            y_raw = ((y_bytes[1] << 8) | y_bytes[2]) >> 3
            
            # Pull CS high to end communication
            self.cs.value(1)
            
            # Check if touch is valid (not at edges)
            if x_raw < 100 or x_raw > 3900 or y_raw < 100 or y_raw > 3900:
                return None
                
            return (x_raw, y_raw)
        except Exception:
            # Make sure CS is high on error
            self.cs.value(1)
            return None
    
    def _normalize(self, x_raw, y_raw):
        """Convert raw coordinates to screen coordinates."""
        # Convert to 0-width/height range
        if self.swap_xy:
            x_raw, y_raw = y_raw, x_raw
        
        screen_x = int((x_raw - self.x_min) * self._x_factor)
        screen_y = int((y_raw - self.y_min) * self._y_factor)
        
        # Apply transformations
        if self.flip_x:
            screen_x = self.width - 1 - screen_x
        if self.flip_y:
            screen_y = self.height - 1 - screen_y
        
        # Clamp to screen bounds
        screen_x = max(0, min(screen_x, self.width - 1))
        screen_y = max(0, min(screen_y, self.height - 1))
    
        return screen_x, screen_y
    
    def _touch_irq_handler(self, pin):
        """Interrupt handler - starts/stops timer polling based on touch state."""
        try:
            current_time = ticks_ms()
            if ticks_diff(current_time, self._last_irq_time) > self._irq_debounce_ms:
                self._last_irq_time = current_time
                
                # Check current touch state
                is_touch_down_now = not self.irq_pin.value()
                
                # Case 1: Touch just started
                if is_touch_down_now and not self._touch_down:
                    raw_pos = self._raw_touch()
                    if raw_pos:
                        screen_x, screen_y = self._normalize(raw_pos[0], raw_pos[1])
                        self._touch_down = True
                        self._start_x = screen_x
                        self._start_y = screen_y
                        self._current_touch_x = screen_x
                        self._current_touch_y = screen_y
                        self._is_currently_touched = True
                        self._touch_positions = [(screen_x, screen_y, ticks_ms())]
                        
                        # Start the polling timer
                        # We need this because when the touch ends we can no longer
                        # retrieve touch positions, so to detect a swipe we need to
                        # poll while the finger is down
                        self._start_timer_polling()
                
                # Case 2: Touch just ended
                elif not is_touch_down_now and self._touch_down:
                    self._touch_down = False
                    self._is_currently_touched = False
                    self._stop_timer_polling()
                    
                    # Process the completed gesture using all collected positions
                    self._process_gesture()
                    self._touch_positions = []
                    
        except Exception:
            pass
    
    def _start_timer_polling(self):
        """Start the hardware timer for touch position polling."""
        if not self._timer_active:
            self._timer_active = True
            self._timer.init(period=10, mode=Timer.PERIODIC, callback=self._timer_poll_callback)
    
    def _stop_timer_polling(self):
        """Stop the hardware timer polling."""
        if self._timer_active:
            self._timer_active = False
            self._timer.deinit()
    
    def _timer_poll_callback(self, timer):
        """Timer callback to poll touch positions while finger is down."""
        try:
            if self._touch_down:
                raw_pos = self._raw_touch()
                if raw_pos:
                    screen_x, screen_y = self._normalize(raw_pos[0], raw_pos[1])
                    self._current_touch_x = screen_x
                    self._current_touch_y = screen_y
                    
                    current_time = ticks_ms()
                    self._touch_positions.append((screen_x, screen_y, current_time))
                    
                    # Limit position history to prevent memory issues
                    if len(self._touch_positions) > 50:
                        self._touch_positions = self._touch_positions[-25:]
            else:
                # Touch ended
                self._stop_timer_polling()
                
        except Exception:
            pass
    
    def _process_gesture(self):
        """Process the completed gesture using all collected touch positions."""
        if not self._touch_positions or len(self._touch_positions) < 1:
            return
        
        start_x, start_y, start_time = self._touch_positions[0]
        end_x, end_y, end_time = self._touch_positions[-1]
        
        # Store start position for bounds checking in was_swiped()
        self._start_x = start_x
        self._start_y = start_y
        
        # Calculate total movement
        dx = end_x - start_x
        dy = end_y - start_y
        distance = (dx*dx + dy*dy)**0.5
        
        self._last_touch_x = end_x
        self._last_touch_y = end_y
        
        # Classify gesture based on distance
        if distance <= MAX_TAP_DISTANCE:
            self._was_touched = True
            self._touch_count += 1  # Increment counter for get_touches()
        elif distance >= MIN_SWIPE_DISTANCE:
            abs_dx = abs(dx)
            abs_dy = abs(dy)
            
            if abs_dx > abs_dy:
                if dx > 0:
                    self._was_swiped_right = True
                else:
                    self._was_swiped_left = True
            else:
                if dy > 0:
                    self._was_swiped_down = True
                else:
                    self._was_swiped_up = True
        # If between 8-30 pixels, it's in the dead zone - ignore
    
    # --- Public API Methods ---
    
    def is_touched(self):
        """Check if the screen is currently being touched.
        
        Returns:
            dict or None: {'x': x_coord, 'y': y_coord} if touched, None if not
        """
        if self._is_currently_touched:
            return {
                'x': self._current_touch_x,
                'y': self._current_touch_y
            }
        return None
    
    def was_touched(self):
        """Check if a touch (tap) occurred since the last call to this method.
        
        A touch is defined as a press-release with movement <= 8 pixels.
        This method consumes the event (micro:bit style behavior).
        
        Returns:
            bool: True if a new touch was detected since last call
        """
        if self._was_touched:
            self._was_touched = False
            return True
        return False
    
    def get_touches(self):
        """Get the number of touches (taps) since the last call to this method.
        
        Like micro:bit's button.get_presses(), this returns the count of tap events
        and then resets the counter to zero. Only counts taps (movement <= 8 pixels),
        not swipes.
        
        Returns:
            int: Number of taps since last call to this method
        """
        count = self._touch_count
        self._touch_count = 0
        return count
    
    def was_swiped(self, direction=None, bounds=None):
        """Check if a swipe occurred since the last call.
        
        Args:
            direction (str, optional): Specific direction to check ('left', 'right', 'up', 'down').
                                     If None, checks for any swipe direction.
            bounds (tuple, optional): Bounding box (x, y, w, h) to constrain swipe detection.
                                    If None, checks entire screen area.
        
        Returns:
            bool: True if a swipe matching the criteria was detected since last call
        """
        # Check if any swipe occurred
        any_swipe = (self._was_swiped_left or self._was_swiped_right or 
                    self._was_swiped_up or self._was_swiped_down)
        
        if not any_swipe:
            return False
        
        # If bounds are specified, check if the swipe start/end are within bounds
        if bounds is not None:
            x, y, w, h = bounds
            start_in_bounds = (x <= self._start_x <= x + w and y <= self._start_y <= y + h)
            end_in_bounds = (x <= self._last_touch_x <= x + w and y <= self._last_touch_y <= y + h)
            
            # Both start and end must be within bounds
            if not (start_in_bounds and end_in_bounds):
                return False
        
        # Check specific direction if requested
        if direction is None:
            # Any swipe direction matches
            result = any_swipe
        elif direction.lower() == 'left':
            result = self._was_swiped_left
        elif direction.lower() == 'right':
            result = self._was_swiped_right
        elif direction.lower() == 'up':
            result = self._was_swiped_up
        elif direction.lower() == 'down':
            result = self._was_swiped_down
        else:
            # Invalid direction
            return False
        
        # If we found a matching swipe, clear ALL swipe flags (consume the event)
        if result:
            self._was_swiped_left = False
            self._was_swiped_right = False
            self._was_swiped_up = False
            self._was_swiped_down = False
            
        return result
    
    # --- Backward Compatibility Methods ---
    # These methods maintain compatibility with the original individual swipe methods
    
    def was_swiped_left(self):
        """Check if a left swipe occurred (backward compatibility)."""
        return self.was_swiped(direction='left')
    
    def was_swiped_right(self):
        """Check if a right swipe occurred (backward compatibility)."""
        return self.was_swiped(direction='right')
    
    def was_swiped_up(self):
        """Check if an up swipe occurred (backward compatibility)."""
        return self.was_swiped(direction='up')
    
    def was_swiped_down(self):
        """Check if a down swipe occurred (backward compatibility)."""
        return self.was_swiped(direction='down')
    
    def get_last_touch_coords(self):
        """Get the coordinates of the last completed touch (tap).
        
        Returns:
            tuple: (x, y) coordinates of the last touch
        """
        return (self._last_touch_x, self._last_touch_y)
    
    def clear_touch_history(self):
        """Clear all touch event history."""
        self._was_touched = False
        self._was_swiped_up = False
        self._was_swiped_down = False
        self._was_swiped_left = False
        self._was_swiped_right = False
        self._last_touch_x = -1
        self._last_touch_y = -1
        self._touch_count = 0  # Reset touch counter
    
    # --- Calibration Methods ---
    
    def _auto_calibrate_with_display(self):
        """Auto-calibrate using display for visual guidance."""
        if not _display_available:
            print("Display not available for auto-calibration")
            return False
        
        print("Starting interactive touch calibration...")
        
        # Create display instance for calibration
        cal_display = Display()
        cal_display.clear()
        
        # Show calibration instructions
        cal_display.show_text_at(10, 10, "Touch Calibration", "cyan")
        cal_display.show_text_at(10, 40, "Touch each crosshair exactly", "white")
        cal_display.show_text_at(10, 60, "in the center when prompted", "white")
        cal_display.show_text_at(10, 100, "Press and hold for 1 second", "yellow")
        cal_display.show_text_at(10, 120, "to register each point", "yellow")
        
        sleep(3)
        
        # Define calibration points (use actual screen edges for better accuracy)
        cal_points = [
            (20, 20, "Top-Left"),
            (300, 20, "Top-Right"), 
            (300, 220, "Bottom-Right"),
            (20, 220, "Bottom-Left"),
            (160, 120, "Center")
        ]
        
        raw_points = []
        screen_points = []
        
        for i, (screen_x, screen_y, label) in enumerate(cal_points):
            cal_display.clear()
            cal_display.show_text_at(10, 10, f"Calibration {i+1}/5", "cyan")
            cal_display.show_text_at(10, 30, f"Touch: {label}", "white")
            cal_display.show_text_at(10, 50, "Hold for 1 second", "yellow")
            
            # Draw crosshair
            cal_display.draw_line(screen_x-10, screen_y, screen_x+10, screen_y, "red")
            cal_display.draw_line(screen_x, screen_y-10, screen_x, screen_y+10, "red")
            cal_display.draw_circle(screen_x, screen_y, 15, "red")
            
            # Wait for touch and hold
            print(f"Calibrating point {i+1}: {label} at ({screen_x}, {screen_y})")
            
            touch_samples = []
            hold_time = 0
            
            while hold_time < 10:  # Need 1 second hold (10 * 0.1s)
                raw_pos = self._raw_touch()
                irq_val = self.irq_pin.value()
                
                if raw_pos and irq_val == 0:  # Valid touch detected
                    touch_samples.append(raw_pos)
                    hold_time += 1
                    
                    # Visual feedback
                    cal_display.show_text_at(10, 200, f"Holding... {hold_time}/10", "green")
                else:
                    # Reset if touch is lost
                    touch_samples = []
                    hold_time = 0
                    cal_display.show_text_at(10, 200, "Touch and hold target", "yellow")
                    
                sleep(0.1)
            
            # Calculate average of samples for this point
            if touch_samples:
                avg_x = sum(p[0] for p in touch_samples) // len(touch_samples)
                avg_y = sum(p[1] for p in touch_samples) // len(touch_samples)
                raw_points.append((avg_x, avg_y))
                screen_points.append((screen_x, screen_y))
                
                cal_display.show_text_at(10, 220, "Point captured!", "green")
                print(f"Captured raw point: ({avg_x}, {avg_y}) -> screen: ({screen_x}, {screen_y})")
                sleep(1)
            else:
                cal_display.show_text_at(10, 220, "Failed to capture point", "red")
                sleep(2)
                return False
        
        # Calculate calibration parameters
        if len(raw_points) >= 4:  # Need at least 4 points
            # STEP 1: Determine coordinate orientations using raw points
            raw_xs = [p[0] for p in raw_points[:4]]  # First 4 are corners  
            raw_ys = [p[1] for p in raw_points[:4]]
            
            # Determine swap_xy first by comparing coordinate ranges
            raw_x_range = max(raw_xs) - min(raw_xs)
            raw_y_range = max(raw_ys) - min(raw_ys)
            # If raw Y range > raw X range, then coordinates are swapped
            self.swap_xy = raw_y_range > raw_x_range
            
            # STEP 2: Apply coordinate transformations to get correct bounds
            transformed_points = []
            for raw_x, raw_y in raw_points[:4]:  # First 4 are corners
                # Apply swap transformation (same as in _normalize)
                if self.swap_xy:
                    raw_x, raw_y = raw_y, raw_x
                transformed_points.append((raw_x, raw_y))
            
            # Use transformed coordinates for bounds calculation
            trans_xs = [p[0] for p in transformed_points]
            trans_ys = [p[1] for p in transformed_points]
            
            # Get the coordinate bounds from our transformed calibration points
            raw_x_min = min(trans_xs)
            raw_x_max = max(trans_xs)
            raw_y_min = min(trans_ys)
            raw_y_max = max(trans_ys)
            
            # Our calibration points are at screen positions:
            # (20, 20), (300, 20), (300, 220), (20, 220)
            # We need to extrapolate to full screen (0, 0) to (320, 240)
            
            # Calculate scaling factors from our calibration area
            cal_screen_width = 300 - 20  # 280 pixels
            cal_screen_height = 220 - 20  # 200 pixels
            raw_width = raw_x_max - raw_x_min
            raw_height = raw_y_max - raw_y_min
            
            # Calculate raw coordinates per screen pixel
            raw_per_screen_x = raw_width / cal_screen_width
            raw_per_screen_y = raw_height / cal_screen_height
            
            # Extrapolate to full screen bounds
            # For X: calibration goes from screen X=20 to X=300 (280 pixel span)
            # Need to extrapolate to X=0 to X=320
            self.x_min = int(raw_x_min - (20 * raw_per_screen_x))
            self.x_max = int(raw_x_max + (20 * raw_per_screen_x))  # 320-300=20
            
            # For Y: calibration goes from screen Y=20 to Y=220 (200 pixel span)  
            # Need to extrapolate to Y=0 to Y=240
            self.y_min = int(raw_y_min - (20 * raw_per_screen_y))
            self.y_max = int(raw_y_max + (20 * raw_per_screen_y))  # 240-220=20
            
            # STEP 3: Determine flip orientations using original raw points
            # Points: [top-left, top-right, bottom-right, bottom-left, center]
            # Screen positions: [(20,20), (300,20), (300,220), (20,220), (160,120)]
            top_left_raw = raw_points[0]     # Should map to (20, 20)
            top_right_raw = raw_points[1]    # Should map to (300, 20)
            bottom_right_raw = raw_points[2] # Should map to (300, 220)
            bottom_left_raw = raw_points[3]  # Should map to (20, 220)
            
            # Check X orientation: if raw X increases from left to right, no flip needed
            # Compare left points (20 screen X) vs right points (300 screen X)
            if self.swap_xy:
                # If swapped, use Y coordinates for X comparison
                left_raw_x = (top_left_raw[1] + bottom_left_raw[1]) / 2
                right_raw_x = (top_right_raw[1] + bottom_right_raw[1]) / 2
            else:
                # Normal X coordinates
                left_raw_x = (top_left_raw[0] + bottom_left_raw[0]) / 2
                right_raw_x = (top_right_raw[0] + bottom_right_raw[0]) / 2
            self.flip_x = left_raw_x > right_raw_x  # Flip if left raw > right raw
            
            # Check Y orientation: if raw Y increases from top to bottom, no flip needed
            # Compare top points (20 screen Y) vs bottom points (220 screen Y)
            if self.swap_xy:
                # If swapped, use X coordinates for Y comparison
                top_raw_y = (top_left_raw[0] + top_right_raw[0]) / 2
                bottom_raw_y = (bottom_right_raw[0] + bottom_left_raw[0]) / 2
            else:
                # Normal Y coordinates
                top_raw_y = (top_left_raw[1] + top_right_raw[1]) / 2
                bottom_raw_y = (bottom_right_raw[1] + bottom_left_raw[1]) / 2
            self.flip_y = bottom_raw_y < top_raw_y  # Flip if bottom raw < top raw
            
            self._recalculate_factors()
            self._save_calibration()
            
            # Show results
            cal_display.clear()
            cal_display.show_text_at(10, 10, "Calibration Complete!", "green")
            cal_display.show_text_at(10, 40, f"X: {self.x_min}-{self.x_max}", "white")
            cal_display.show_text_at(10, 60, f"Y: {self.y_min}-{self.y_max}", "white")
            cal_display.show_text_at(10, 80, f"Flip X: {self.flip_x}", "white")
            cal_display.show_text_at(10, 100, f"Flip Y: {self.flip_y}", "white")
            cal_display.show_text_at(10, 120, f"Swap XY: {self.swap_xy}", "white")
            cal_display.show_text_at(10, 160, "Touch anywhere to test", "yellow")
            
            print("Calibration completed successfully!")
            print(f"Bounds: X({self.x_min}-{self.x_max}), Y({self.y_min}-{self.y_max})")
            print(f"Transform: flip_x={self.flip_x}, flip_y={self.flip_y}, swap_xy={self.swap_xy}")
            
            sleep(3)
            cal_display.clear()
            return True
        else:
            cal_display.clear()
            cal_display.show_text_at(10, 10, "Calibration Failed", "red")
            cal_display.show_text_at(10, 40, "Not enough points captured", "white")
            sleep(3)
            cal_display.clear()
            return False
    
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
    
    def force_calibration(self):
        """Force a new calibration sequence, ignoring any saved calibration."""
        if _display_available:
            print("Starting forced calibration...")
            return self._auto_calibrate_with_display()
        else:
            print("Display not available for calibration")
            return False
    
    def test_coordinates(self):
        """Test coordinate accuracy by showing raw and screen coordinates."""
        print("Touch Coordinate Test")
        print("Touch the screen to test coordinate accuracy.")
        print("Shows: Raw -> Screen coordinates")
        print("Ctrl+C to exit.")
        print("=" * 40)
        
        try:
            last_touch_time = 0
            while True:
                # Check for current touch
                current = self.is_touched()
                raw = self._raw_touch()
                irq_val = self.irq_pin.value()
                
                current_time = ticks_ms()
                
                if current and raw:
                    # Only print if enough time has passed to avoid spam
                    if ticks_diff(current_time, last_touch_time) > 200:  # 200ms between prints
                        print(f"Raw: ({raw[0]:4d}, {raw[1]:4d}) -> Screen: ({current['x']:3d}, {current['y']:3d}) | IRQ: {irq_val}")
                        last_touch_time = current_time
                
                sleep(0.05)
        except KeyboardInterrupt:
            print("\nCoordinate test ended.")
    
    def get_raw_coordinates(self):
        """Get current raw touch coordinates (for advanced debugging).
        
        Returns:
            tuple or None: (x_raw, y_raw) if touched, None if not
        """
        if self._is_currently_touched:
            return self._raw_touch()
        return None
    
    def debug_touch_hardware(self):
        """Debug method to test basic touch hardware functionality."""
        print("=== Touch Hardware Debug ===")
        print(f"IRQ Pin (36) value: {self.irq_pin.value()}")
        print("Touch the screen now...")
        
        for i in range(50):  # 5 seconds of testing
            irq_val = self.irq_pin.value()
            raw_pos = self._raw_touch()
            
            if raw_pos:
                print(f"IRQ: {irq_val}, Raw: {raw_pos[0]:4d},{raw_pos[1]:4d}")
            elif irq_val == 0:  # IRQ is active but no valid touch
                print(f"IRQ: {irq_val}, Raw: None (invalid)")
            
            sleep(0.1)
        
        print("Debug test complete.")
    
    def debug_interrupt_handler(self):
        """Debug method to monitor interrupt activity."""
        print("=== Interrupt Handler Debug ===")
        print("Monitoring interrupts for 10 seconds...")
        
        self._debug_irq_count = 0
        
        def debug_irq_handler(pin):
            self._debug_irq_count += 1
            irq_val = pin.value()
            print(f"IRQ #{self._debug_irq_count}: Pin value = {irq_val}")
        
        # Temporarily replace the handler
        original_handler = self._touch_irq_handler
        self.irq_pin.irq(handler=debug_irq_handler)
        
        try:
            sleep(10)
        finally:
            # Restore original handler
            self.irq_pin.irq(handler=original_handler)
            print(f"Total interrupts detected: {self._debug_irq_count}")
            print("Debug complete - original handler restored.")
