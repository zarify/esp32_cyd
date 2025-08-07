"""
Touch Test Program - Manual testing and visualization
This program provides comprehensive touch testing with visual feedback.

Features:
- Shows touch positions as dots on screen
- Displays start/end points of swipes with lines
- Prints detailed information to console
- Real-time coordinate display
- Gesture classification visualization

Usage:
- Touch screen to see touch dots
- Swipe to see swipe lines and classification
- Press Ctrl+C to exit

Author: ESP32 CYD Touch Library
"""

from src.easy_touch import Touch
from src.easy_display import Display
from time import sleep, ticks_ms, ticks_diff
import sys

class TouchTester:
    """Interactive touch testing with visual feedback."""
    
    def __init__(self):
        """Initialize the touch tester."""
        print("=== Touch Test Program Starting ===")
        
        # Initialize display and touch
        self.display = Display()
        self.touch = Touch()  # Will auto-calibrate if needed
        
        # Test state
        self.last_print_time = 0
        self.gesture_count = 0
        
        # Colors for visualization
        self.colors = {
            'touch_dot': 'cyan',
            'tap_dot': 'green',
            'swipe_line': 'yellow',
            'swipe_start': 'red',
            'swipe_end': 'magenta',
            'text': 'white',
            'info': 'gray'
        }
        
        # Setup initial display
        self.setup_display()
        
    def setup_display(self):
        """Setup the initial display."""
        self.display.clear()
        self.display.show_text_at(5, 5, "Touch Tester", self.colors['text'])
        self.display.show_text_at(5, 25, "Touch to see dots", self.colors['info'])
        self.display.show_text_at(5, 45, "Swipe to see lines", self.colors['info'])
        
    def draw_crosshair(self, x, y, size, color):
        """Draw a crosshair at the specified position."""
        self.display.draw_line(x-size, y, x+size, y, color)
        self.display.draw_line(x, y-size, x, y+size, color)
        
    def draw_touch_dot(self, x, y, radius=3):
        """Draw a dot where touch occurred."""
        if 0 <= x < 320 and 0 <= y < 240:  # Ensure within screen bounds
            self.display.fill_circle(x, y, radius, self.colors['touch_dot'])
            
    def draw_tap_feedback(self, x, y):
        """Draw feedback for a tap gesture."""
        if 0 <= x < 320 and 0 <= y < 240:
            # Draw larger circle for tap
            self.display.draw_circle(x, y, 8, self.colors['tap_dot'])
            self.display.fill_circle(x, y, 3, self.colors['tap_dot'])
            
    def draw_swipe_feedback(self, start_x, start_y, end_x, end_y, direction):
        """Draw feedback for a swipe gesture."""
        # Ensure coordinates are within bounds
        start_x = max(0, min(319, start_x))
        start_y = max(0, min(239, start_y))
        end_x = max(0, min(319, end_x))
        end_y = max(0, min(239, end_y))
        
        # Draw line from start to end
        self.display.draw_line(start_x, start_y, end_x, end_y, self.colors['swipe_line'])
        
        # Draw start point (red crosshair)
        self.draw_crosshair(start_x, start_y, 5, self.colors['swipe_start'])
        
        # Draw end point (magenta crosshair)
        self.draw_crosshair(end_x, end_y, 5, self.colors['swipe_end'])
        
        # Draw direction arrow
        self.draw_direction_arrow(start_x, start_y, end_x, end_y, direction)
        
    def draw_direction_arrow(self, start_x, start_y, end_x, end_y, direction):
        """Draw an arrow indicating swipe direction."""
        # Calculate arrow position (1/3 along the line from start)
        arrow_x = start_x + (end_x - start_x) // 3
        arrow_y = start_y + (end_y - start_y) // 3
        
        # Draw arrow based on direction
        arrow_size = 8
        if direction == 'right':
            # Right arrow: >
            self.display.draw_line(arrow_x, arrow_y, arrow_x + arrow_size, arrow_y - 4, self.colors['swipe_line'])
            self.display.draw_line(arrow_x, arrow_y, arrow_x + arrow_size, arrow_y + 4, self.colors['swipe_line'])
        elif direction == 'left':
            # Left arrow: <
            self.display.draw_line(arrow_x, arrow_y, arrow_x - arrow_size, arrow_y - 4, self.colors['swipe_line'])
            self.display.draw_line(arrow_x, arrow_y, arrow_x - arrow_size, arrow_y + 4, self.colors['swipe_line'])
        elif direction == 'up':
            # Up arrow: ^
            self.display.draw_line(arrow_x, arrow_y, arrow_x - 4, arrow_y - arrow_size, self.colors['swipe_line'])
            self.display.draw_line(arrow_x, arrow_y, arrow_x + 4, arrow_y - arrow_size, self.colors['swipe_line'])
        elif direction == 'down':
            # Down arrow: v
            self.display.draw_line(arrow_x, arrow_y, arrow_x - 4, arrow_y + arrow_size, self.colors['swipe_line'])
            self.display.draw_line(arrow_x, arrow_y, arrow_x + 4, arrow_y + arrow_size, self.colors['swipe_line'])
            
    def print_with_throttle(self, message, min_interval_ms=100):
        """Print message with time throttling to avoid spam."""
        current_time = ticks_ms()
        if ticks_diff(current_time, self.last_print_time) >= min_interval_ms:
            print(message)
            self.last_print_time = current_time
            
    def run_test(self):
        """Run the interactive touch test."""
        print("Touch Test Running...")
        print("- Touch screen to see position dots")
        print("- Swipe to see gesture lines and classification")
        print("- All gestures are logged to console")
        print("- Press Ctrl+C to exit")
        print("=" * 50)
        
        try:
            while True:
                # Check for current touch position
                current_touch = self.touch.is_touched()
                if current_touch:
                    x, y = current_touch['x'], current_touch['y']
                    self.draw_touch_dot(x, y, 2)
                    
                    # Print current position (throttled)
                    raw_pos = self.touch.get_raw_coordinates()
                    if raw_pos:
                        self.print_with_throttle(f"Touch: Raw({raw_pos[0]:4d}, {raw_pos[1]:4d}) -> Screen({x:3d}, {y:3d})", 200)
                    
                # Check for completed gestures
                if self.touch.was_touched():
                    self.gesture_count += 1
                    coords = self.touch.get_last_touch_coords()
                    self.draw_tap_feedback(coords[0], coords[1])
                    print(f"[{self.gesture_count}] TAP at ({coords[0]}, {coords[1]})")
                    
                # Check for swipes in all directions
                if self.touch.was_swiped(direction='left'):
                    self.gesture_count += 1
                    coords = self.touch.get_last_touch_coords()
                    # Get start position from touch internals if available
                    start_x = getattr(self.touch, '_start_x', coords[0] + 30)  # Fallback estimate
                    start_y = getattr(self.touch, '_start_y', coords[1])
                    self.draw_swipe_feedback(start_x, start_y, coords[0], coords[1], 'left')
                    print(f"[{self.gesture_count}] LEFT SWIPE: ({start_x}, {start_y}) -> ({coords[0]}, {coords[1]})")
                    
                elif self.touch.was_swiped(direction='right'):
                    self.gesture_count += 1
                    coords = self.touch.get_last_touch_coords()
                    start_x = getattr(self.touch, '_start_x', coords[0] - 30)
                    start_y = getattr(self.touch, '_start_y', coords[1])
                    self.draw_swipe_feedback(start_x, start_y, coords[0], coords[1], 'right')
                    print(f"[{self.gesture_count}] RIGHT SWIPE: ({start_x}, {start_y}) -> ({coords[0]}, {coords[1]})")
                    
                elif self.touch.was_swiped(direction='up'):
                    self.gesture_count += 1
                    coords = self.touch.get_last_touch_coords()
                    start_x = getattr(self.touch, '_start_x', coords[0])
                    start_y = getattr(self.touch, '_start_y', coords[1] + 30)
                    self.draw_swipe_feedback(start_x, start_y, coords[0], coords[1], 'up')
                    print(f"[{self.gesture_count}] UP SWIPE: ({start_x}, {start_y}) -> ({coords[0]}, {coords[1]})")
                    
                elif self.touch.was_swiped(direction='down'):
                    self.gesture_count += 1
                    coords = self.touch.get_last_touch_coords()
                    start_x = getattr(self.touch, '_start_x', coords[0])
                    start_y = getattr(self.touch, '_start_y', coords[1] - 30)
                    self.draw_swipe_feedback(start_x, start_y, coords[0], coords[1], 'down')
                    print(f"[{self.gesture_count}] DOWN SWIPE: ({start_x}, {start_y}) -> ({coords[0]}, {coords[1]})")
                
                # Check touch counter
                touch_count = self.touch.get_touches()
                if touch_count > 0:
                    print(f"Touch counter: {touch_count} accumulated taps")
                    
                sleep(0.02)  # 50 FPS update rate
                
        except KeyboardInterrupt:
            print("\n" + "=" * 50)
            print("Touch test ended by user")
            print(f"Total gestures detected: {self.gesture_count}")
            
            # Show final summary screen
            self.display.clear()
            self.display.show_text_at(10, 10, "Test Complete", self.colors['text'])
            self.display.show_text_at(10, 40, f"Gestures: {self.gesture_count}", self.colors['info'])
            self.display.show_text_at(10, 60, "Check console for logs", self.colors['info'])
            
        except Exception as e:
            print(f"Test error: {e}")
            self.display.clear()
            self.display.show_text_at(10, 10, "Test Error", 'red')
            self.display.show_text_at(10, 30, str(e)[:30], 'red')

def main():
    """Main entry point for the touch tester."""
    print("Starting Touch Test Program...")
    
    # Check if we should force calibration
    if len(sys.argv) > 1 and sys.argv[1] == "--calibrate":
        print("Forcing new calibration...")
        touch = Touch(auto_calibrate=False)  # Don't auto-calibrate
        success = touch.force_calibration()
        if not success:
            print("Calibration failed!")
            return
        print("Calibration complete, starting test...")
    
    # Run the test
    tester = TouchTester()
    tester.run_test()

if __name__ == "__main__":
    main()
else:
    print("Touch tester imported - call main() to run")
