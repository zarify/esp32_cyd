"""
Touch Library Demo - Comprehensive demonstration of all touch capabilities
This demo validates all touch methods and provides visual feedback using easy_display.

Run this as a standalone demo or copy to boot.py to run automatically on device startup.
The demo will guide you through each touch capability and wait for you to perform
the required actions before proceeding to the next test.

Author: ESP32 CYD Touch Library
"""

from easy_touch import Touch
from easy_display import Display
from time import sleep

class TouchDemo:
    """Interactive touch demonstration and validation."""
    
    def __init__(self):
        """Initialize the demo with display and touch interfaces."""
        print("=== Touch Library Demo Starting ===")
        
        # Initialize display and touch
        self.display = Display()
        self.touch = Touch()  # Auto-calibration will run if needed
        
        # Demo state
        self.current_step = 0
        self.total_steps = 8
        
        # Colors for different states
        self.colors = {
            'title': 'cyan',
            'instruction': 'white', 
            'success': 'green',
            'waiting': 'yellow',
            'info': 'gray'
        }
        
    def show_header(self, title, step_num):
        """Display demo section header."""
        self.display.clear()
        self.display.show_text_at(10, 10, f"Touch Demo - Step {step_num}/{self.total_steps}", self.colors['info'])
        self.display.show_text_at(10, 30, title, self.colors['title'])
        self.display.show_text_at(10, 50, "=" * 35, self.colors['info'])
        
    def clear_region(self, x, y, width, height):
        """Clear a specific region of the screen efficiently."""
        self.display.fill_rectangle(x, y, width, height, 'black')
        
    def show_instruction(self, text, y_pos=70):
        """Display instruction text."""
        # Handle multi-line instructions
        lines = text.split('\n')
        for i, line in enumerate(lines):
            self.display.show_text_at(10, y_pos + (i * 20), line, self.colors['instruction'])
    
    def show_success(self, text, y_pos=160):
        """Display success message."""
        # Clear the area where success message will be displayed
        self.clear_region(10, y_pos, 300, 20)
        self.display.show_text_at(10, y_pos, text, self.colors['success'])
        
    def show_waiting(self, text, y_pos=200):
        """Display waiting message."""
        self.display.show_text_at(10, y_pos, text, self.colors['waiting'])
        
    def wait_for_any_touch_to_continue(self):
        """Wait for user to tap to continue."""
        self.show_waiting("Tap anywhere to continue...")
        while True:
            if self.touch.was_touched():
                break
            sleep(0.05)
        sleep(0.5)  # Brief pause before next section
        # Clear any remaining touch history before next demo
        self.touch.clear_touch_history()
        
    def demo_1_current_touch_detection(self):
        """Demo 1: Test is_touched() method for current touch detection."""
        self.current_step += 1
        self.touch.clear_touch_history()  # Clear any previous touch events
        self.show_header("Current Touch Detection", self.current_step)
        self.show_instruction("Touch and hold different areas\nof the screen. Watch coordinates\nupdate in real-time.")
        
        touch_count = 0
        last_pos = None
        last_displayed_pos = None
        
        # Show initial waiting message
        self.show_waiting("Touch the screen now...")
        
        while touch_count < 5:  # Require 5 different touch positions
            current = self.touch.is_touched()
            
            if current:
                x, y = current['x'], current['y']
                
                # Only update display if position changed significantly
                if last_displayed_pos is None or (abs(x - last_displayed_pos[0]) > 5 or abs(y - last_displayed_pos[1]) > 5):
                    # Clear only the position info region
                    self.clear_region(10, 120, 300, 40)
                    
                    # Show current position
                    self.display.show_text_at(10, 120, f"Touching at: ({x}, {y})", self.colors['success'])
                    last_displayed_pos = (x, y)
                
                # Count unique positions (rough check)
                if last_pos is None or (abs(x - last_pos[0]) > 20 or abs(y - last_pos[1]) > 20):
                    if last_pos is not None:
                        touch_count += 1
                        # Only update counter when it changes
                        self.display.show_text_at(10, 140, f"Positions touched: {touch_count}/5", self.colors['info'])
                    last_pos = (x, y)
            else:
                # Clear position info when not touching (only if currently displayed)
                if last_displayed_pos is not None:
                    self.clear_region(10, 120, 300, 40)
                    self.display.show_text_at(10, 120, "Not touching", self.colors['waiting'])
                    last_displayed_pos = None
                
            sleep(0.05)
            
        self.show_success("[OK] Current touch detection works!")
        self.wait_for_any_touch_to_continue()
        
    def demo_2_tap_detection(self):
        """Demo 2: Test was_touched() method for tap detection."""
        self.current_step += 1
        self.touch.clear_touch_history()  # Clear any previous touch events
        self.show_header("Tap Detection", self.current_step)
        self.show_instruction("Make quick taps on the screen.\nEach tap should be detected\nand counted.")
        
        tap_count = 0
        target_taps = 5
        
        while tap_count < target_taps:
            if self.touch.was_touched():
                tap_count += 1
                coords = self.touch.get_last_touch_coords()
                
                # Clear only the info region
                self.clear_region(10, 120, 300, 60)
                
                # Show tap info
                self.display.show_text_at(10, 120, f"Tap #{tap_count} at {coords}", self.colors['success'])
                self.display.show_text_at(10, 140, f"Taps: {tap_count}/{target_taps}", self.colors['info'])
                
                # Brief visual feedback - use proper coordinates
                if coords[0] >= 0 and coords[1] >= 0:  # Ensure valid coordinates
                    self.display.fill_circle(coords[0], coords[1], 5, 'green')
                    sleep(0.2)
                    self.display.fill_circle(coords[0], coords[1], 5, 'black')
                
            sleep(0.05)
            
        self.show_success("[OK] Tap detection works!")
        self.wait_for_any_touch_to_continue()
        
    def demo_3_touch_counter(self):
        """Demo 3: Test get_touches() method (micro:bit style counter)."""
        self.current_step += 1
        self.touch.clear_touch_history()  # Clear any previous touch events
        self.show_header("Touch Counter", self.current_step)
        self.show_instruction("Make several quick taps, then\nwait. The counter will show\nhow many taps occurred.")
        
        demo_cycles = 3
        current_cycle = 0
        
        while current_cycle < demo_cycles:
            self.clear_region(10, 120, 300, 80)
            self.show_waiting(f"Cycle {current_cycle + 1}/{demo_cycles}: Tap rapidly!")
            
            # Wait for some taps to accumulate
            start_time = 0
            while start_time < 30:  # 3 seconds of tapping opportunity
                # Show any individual taps for feedback
                if self.touch.was_touched():
                    coords = self.touch.get_last_touch_coords()
                    # Use proper coordinates for visual feedback
                    if coords[0] >= 0 and coords[1] >= 0:
                        self.display.fill_circle(coords[0], coords[1], 3, 'yellow')
                    
                start_time += 1
                sleep(0.1)
                
            # Check accumulated count
            tap_count = self.touch.get_touches()
            
            self.clear_region(10, 160, 300, 20)  # Only clear one line, not 40 pixels
            if tap_count > 0:
                self.display.show_text_at(10, 160, f"Counted {tap_count} taps!", self.colors['success'])
                current_cycle += 1
            else:
                self.display.show_text_at(10, 160, "No taps detected, try again", self.colors['waiting'])
                
            sleep(1)
            
        self.show_success("[OK] Touch counter works!", 180)  # Use lower position to avoid conflict
        self.wait_for_any_touch_to_continue()
        
    def demo_4_left_right_swipes(self):
        """Demo 4: Test horizontal swipe detection."""
        self.current_step += 1
        self.touch.clear_touch_history()  # Clear any previous touch events
        self.show_header("Horizontal Swipes", self.current_step)
        self.show_instruction("Swipe LEFT and RIGHT across\nthe screen. Each direction\nwill be detected separately.")
        
        left_swipes = 0
        right_swipes = 0
        target_each = 2
        
        while left_swipes < target_each or right_swipes < target_each:
            # Only update status when it changes
            self.clear_region(10, 120, 300, 60)
            self.display.show_text_at(10, 120, f"Left swipes: {left_swipes}/{target_each}", 
                                    self.colors['success'] if left_swipes >= target_each else self.colors['waiting'])
            self.display.show_text_at(10, 140, f"Right swipes: {right_swipes}/{target_each}", 
                                    self.colors['success'] if right_swipes >= target_each else self.colors['waiting'])
            
            # Check for swipes
            if self.touch.was_swiped(direction='left'):
                left_swipes += 1
                self.display.show_text_at(10, 180, "LEFT swipe detected! <-", self.colors['success'])
                sleep(0.5)
                self.clear_region(10, 180, 300, 20)
                
            elif self.touch.was_swiped(direction='right'):
                right_swipes += 1
                self.display.show_text_at(10, 180, "RIGHT swipe detected! ->", self.colors['success'])
                sleep(0.5)
                self.clear_region(10, 180, 300, 20)
                
            sleep(0.05)
            
        # Ensure final status is displayed
        self.clear_region(10, 120, 300, 60)
        self.display.show_text_at(10, 120, f"Left swipes: {left_swipes}/{target_each}", self.colors['success'])
        self.display.show_text_at(10, 140, f"Right swipes: {right_swipes}/{target_each}", self.colors['success'])
        
        self.show_success("[OK] Horizontal swipes work!")
        self.wait_for_any_touch_to_continue()
        
    def demo_5_up_down_swipes(self):
        """Demo 5: Test vertical swipe detection."""
        self.current_step += 1
        self.touch.clear_touch_history()  # Clear any previous touch events
        self.show_header("Vertical Swipes", self.current_step)
        self.show_instruction("Swipe UP and DOWN on the\nscreen. Each direction will\nbe detected separately.")
        
        up_swipes = 0
        down_swipes = 0
        target_each = 2
        
        while up_swipes < target_each or down_swipes < target_each:
            # Only update status when it changes
            self.clear_region(10, 120, 300, 60)
            self.display.show_text_at(10, 120, f"Up swipes: {up_swipes}/{target_each}", 
                                    self.colors['success'] if up_swipes >= target_each else self.colors['waiting'])
            self.display.show_text_at(10, 140, f"Down swipes: {down_swipes}/{target_each}", 
                                    self.colors['success'] if down_swipes >= target_each else self.colors['waiting'])
            
            # Check for swipes
            if self.touch.was_swiped(direction='up'):
                up_swipes += 1
                self.display.show_text_at(10, 180, "UP swipe detected! ^", self.colors['success'])
                sleep(0.5)
                self.clear_region(10, 180, 300, 20)
                
            elif self.touch.was_swiped(direction='down'):
                down_swipes += 1
                self.display.show_text_at(10, 180, "DOWN swipe detected! v", self.colors['success'])
                sleep(0.5)
                self.clear_region(10, 180, 300, 20)
                
            sleep(0.05)
            
        # Ensure final status is displayed
        self.clear_region(10, 120, 300, 60)
        self.display.show_text_at(10, 120, f"Up swipes: {up_swipes}/{target_each}", self.colors['success'])
        self.display.show_text_at(10, 140, f"Down swipes: {down_swipes}/{target_each}", self.colors['success'])
        
        self.show_success("[OK] Vertical swipes work!")
        self.wait_for_any_touch_to_continue()
        
    def demo_6_any_swipe_detection(self):
        """Demo 6: Test detection of any swipe direction."""
        self.current_step += 1
        self.touch.clear_touch_history()  # Clear any previous touch events
        self.show_header("Any Direction Swipes", self.current_step)
        self.show_instruction("Swipe in ANY direction.\nThe system will detect any\nswipe regardless of direction.")
        
        any_swipes = 0
        target_swipes = 4
        
        while any_swipes < target_swipes:
            # Only update status when it changes
            self.clear_region(10, 120, 300, 40)
            self.display.show_text_at(10, 120, f"Any swipes: {any_swipes}/{target_swipes}", self.colors['info'])
            
            # Check for any swipe
            if self.touch.was_swiped():  # No direction specified = any direction
                any_swipes += 1
                self.display.show_text_at(10, 160, f"Swipe #{any_swipes} detected!", self.colors['success'])
                sleep(0.5)
                self.clear_region(10, 160, 300, 20)
                
            sleep(0.05)
            
        self.show_success("[OK] Any-direction swipes work!")
        self.wait_for_any_touch_to_continue()
        
    def demo_7_bounded_swipes(self):
        """Demo 7: Test swipe detection within specific bounds."""
        self.current_step += 1
        self.touch.clear_touch_history()  # Clear any previous touch events
        self.show_header("Bounded Swipe Detection", self.current_step)
        
        # Define larger test areas to accommodate 30-pixel minimum swipe distance
        left_area = (20, 80, 120, 80)  # x, y, w, h - left side, larger area
        right_area = (180, 80, 120, 80)  # right side, larger area
        
        # Draw the areas
        self.display.draw_rectangle(left_area[0], left_area[1], left_area[2], left_area[3], 'cyan')
        self.display.draw_rectangle(right_area[0], right_area[1], right_area[2], right_area[3], 'magenta')
        
        self.show_instruction("Swipe INSIDE the colored boxes.\nLeft box (cyan) and right box\n(magenta). Swipes outside\nwon't count. Need 30+ pixels.", 180)
        
        left_swipes = 0
        right_swipes = 0
        target_each = 2
        
        while left_swipes < target_each or right_swipes < target_each:
            # Only update status when it changes
            self.clear_region(10, 120, 300, 50)
            self.display.show_text_at(10, 120, f"Left area: {left_swipes}/{target_each}", 
                                    self.colors['success'] if left_swipes >= target_each else self.colors['waiting'])
            self.display.show_text_at(10, 135, f"Right area: {right_swipes}/{target_each}", 
                                    self.colors['success'] if right_swipes >= target_each else self.colors['waiting'])
            
            # Check for bounded swipes
            if self.touch.was_swiped(bounds=left_area):
                left_swipes += 1
                self.display.show_text_at(10, 220, "Left area swipe!", self.colors['success'])
                sleep(0.5)
                self.clear_region(10, 220, 300, 20)
                
            elif self.touch.was_swiped(bounds=right_area):
                right_swipes += 1
                self.display.show_text_at(10, 220, "Right area swipe!", self.colors['success'])
                sleep(0.5)
                self.clear_region(10, 220, 300, 20)
                
            sleep(0.05)
            
        # Ensure final status is displayed
        self.clear_region(10, 120, 300, 50)
        self.display.show_text_at(10, 120, f"Left area: {left_swipes}/{target_each}", self.colors['success'])
        self.display.show_text_at(10, 135, f"Right area: {right_swipes}/{target_each}", self.colors['success'])
        
        self.show_success("[OK] Bounded swipe detection works!")
        self.wait_for_any_touch_to_continue()
        
    def demo_8_comprehensive_test(self):
        """Demo 8: Comprehensive test of multiple features together."""
        self.current_step += 1
        self.touch.clear_touch_history()  # Clear any previous touch events
        self.show_header("Comprehensive Test", self.current_step)
        self.show_instruction("Final test: Use ALL gestures!\n- 2 taps\n- 1 left swipe\n- 1 right swipe\n- 1 up/down swipe")
        
        # Track all required gestures
        taps_needed = 2
        left_swipes_needed = 1
        right_swipes_needed = 1
        vertical_swipes_needed = 1
        
        taps_done = 0
        left_swipes_done = 0
        right_swipes_done = 0
        vertical_swipes_done = 0
        
        # Track last displayed state to avoid unnecessary updates
        last_state = None
        
        while (taps_done < taps_needed or left_swipes_done < left_swipes_needed or 
               right_swipes_done < right_swipes_needed or vertical_swipes_done < vertical_swipes_needed):
            
            # Progress indicators
            tap_status = "OK" if taps_done >= taps_needed else f"{taps_done}/{taps_needed}"
            left_status = "OK" if left_swipes_done >= left_swipes_needed else f"{left_swipes_done}/{left_swipes_needed}"
            right_status = "OK" if right_swipes_done >= right_swipes_needed else f"{right_swipes_done}/{right_swipes_needed}"
            vertical_status = "OK" if vertical_swipes_done >= vertical_swipes_needed else f"{vertical_swipes_done}/{vertical_swipes_needed}"
            
            current_state = (tap_status, left_status, right_status, vertical_status)
            
            # Only update display if state changed
            if current_state != last_state:
                self.clear_region(10, 110, 300, 40)
                self.display.show_text_at(10, 110, f"Taps: {tap_status}  Left: {left_status}", self.colors['info'])
                self.display.show_text_at(10, 130, f"Right: {right_status}  Up/Down: {vertical_status}", self.colors['info'])
                last_state = current_state
            
            # Check for gestures
            if self.touch.was_touched() and taps_done < taps_needed:
                taps_done += 1
                self.display.show_text_at(10, 170, "Tap registered!", self.colors['success'])
                sleep(0.3)
                self.clear_region(10, 170, 300, 20)
                
            elif self.touch.was_swiped(direction='left') and left_swipes_done < left_swipes_needed:
                left_swipes_done += 1
                self.display.show_text_at(10, 170, "Left swipe registered!", self.colors['success'])
                sleep(0.3)
                self.clear_region(10, 170, 300, 20)
                
            elif self.touch.was_swiped(direction='right') and right_swipes_done < right_swipes_needed:
                right_swipes_done += 1
                self.display.show_text_at(10, 170, "Right swipe registered!", self.colors['success'])
                sleep(0.3)
                self.clear_region(10, 170, 300, 20)
                
            elif (self.touch.was_swiped(direction='up') or self.touch.was_swiped(direction='down')) and vertical_swipes_done < vertical_swipes_needed:
                vertical_swipes_done += 1
                self.display.show_text_at(10, 170, "Vertical swipe registered!", self.colors['success'])
                sleep(0.3)
                self.clear_region(10, 170, 300, 20)
                
            sleep(0.05)
            
        # All tests complete!
        self.display.clear()
        self.display.show_text_at(10, 10, "*** ALL TESTS PASSED! ***", self.colors['success'])
        self.display.show_text_at(10, 40, "Touch library is working", self.colors['success'])
        self.display.show_text_at(10, 60, "perfectly!", self.colors['success'])
        
        self.display.show_text_at(10, 100, "Validated features:", self.colors['title'])
        self.display.show_text_at(10, 120, "* Current touch detection", self.colors['info'])
        self.display.show_text_at(10, 140, "* Tap detection", self.colors['info'])
        self.display.show_text_at(10, 160, "* Touch counter", self.colors['info'])
        self.display.show_text_at(10, 180, "* All swipe directions", self.colors['info'])
        self.display.show_text_at(10, 200, "* Bounded swipe detection", self.colors['info'])
        
        self.wait_for_any_touch_to_continue()
        
    def run_demo(self):
        """Run the complete touch demonstration."""
        try:
            # Welcome screen
            self.display.clear()
            self.display.show_text_at(10, 10, "Touch Library Demo", self.colors['title'])
            self.display.show_text_at(10, 40, "This demo will test all", self.colors['instruction'])
            self.display.show_text_at(10, 60, "touch capabilities and", self.colors['instruction'])
            self.display.show_text_at(10, 80, "validate functionality.", self.colors['instruction'])
            self.display.show_text_at(10, 120, "Follow the instructions", self.colors['waiting'])
            self.display.show_text_at(10, 140, "for each test.", self.colors['waiting'])
            self.wait_for_any_touch_to_continue()
            
            # Run all demo sections
            self.demo_1_current_touch_detection()
            self.demo_2_tap_detection()
            self.demo_3_touch_counter()
            self.demo_4_left_right_swipes()
            self.demo_5_up_down_swipes()
            self.demo_6_any_swipe_detection()
            self.demo_7_bounded_swipes()
            self.demo_8_comprehensive_test()
            
            # Final success screen
            self.display.clear()
            self.display.show_text_at(10, 10, "Demo Complete!", self.colors['title'])
            self.display.show_text_at(10, 40, "All touch methods are", self.colors['success'])
            self.display.show_text_at(10, 60, "working correctly!", self.colors['success'])
            self.display.show_text_at(10, 100, "The touch library is", self.colors['info'])
            self.display.show_text_at(10, 120, "ready for use in your", self.colors['info'])
            self.display.show_text_at(10, 140, "projects!", self.colors['info'])
            
            print("=== Touch Library Demo Complete ===")
            print("All touch methods validated successfully!")
            
        except KeyboardInterrupt:
            self.display.clear()
            self.display.show_text_at(10, 10, "Demo Cancelled", self.colors['waiting'])
            print("Demo cancelled by user")
            
        except Exception as e:
            self.display.clear()
            self.display.show_text_at(10, 10, "Demo Error:", 'red')
            self.display.show_text_at(10, 30, str(e)[:30], 'red')
            print(f"Demo error: {e}")

# Run the demo when imported or executed
def main():
    """Main entry point for the demo."""
    demo = TouchDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()
else:
    # Auto-run when imported (useful for boot.py)
    print("Touch demo imported - call main() to run demo")
