"""
Network Test Program for ESP32 CYD
Tests easy_radio functionality using display and touch interfaces.

Features:
- Touch interface to change radio groups
- Send 1, 5, or 15 test messages
- Manual receive button to drain queue
- Real-time diagnostic display
- Visual feedback for all operations

Optimizations:
- Touch callback instead of polling for better responsiveness
- Event-driven display updates only when data changes
- Minimal main loop that only checks exit condition
- Efficient message detection via queue size monitoring
"""

try:
    # MicroPython time functions
    from time import ticks_ms, sleep_ms
    def get_timestamp():
        return ticks_ms()
    def delay_ms(ms):
        sleep_ms(ms)
except ImportError:
    # Standard Python fallback
    import time
    def get_timestamp():
        return int(time.time() * 1000)
    def delay_ms(ms):
        time.sleep(ms / 1000.0)

from easy_display import Display
from easy_touch import Touch
from easy_radio import Radio

class NetworkTester:
    """Network testing interface with touch controls."""
    
    def __init__(self):
        """Initialize display, touch, and radio."""
        print("Initializing Network Tester...")
        
        # Initialize hardware
        self.display = Display()
        self.radio = Radio(group=1, queue_size=20)
        
        # Initialize touch with callback - auto-calibration will handle configuration
        self.touch = Touch(on_touch=self._on_touch_callback)
        
        # Test state
        self.current_group = 1
        self.messages_sent = 0
        self.messages_received = 0
        self.last_message = ""
        self.last_sender = ""
        self.queue_count = 0
        self.last_queue_count = 0  # Track queue changes
        
        # State change flags for efficient updates
        self.display_needs_update = True
        self.buttons_need_redraw = True
        self.exit_requested = False
        
        # Colors - use string names for easy_display
        self.WHITE = "white"
        self.BLACK = "black"
        self.BLUE = "blue"
        self.GREEN = "green"
        self.RED = "red"
        self.YELLOW = "yellow"
        self.GRAY = "gray"
        
        # Button definitions (x, y, width, height, label, color)
        self.buttons = {
            'group_1': (10, 80, 50, 40, "G1", self.GREEN if self.current_group == 1 else self.GRAY),
            'group_2': (70, 80, 50, 40, "G2", self.GRAY),
            'group_5': (130, 80, 50, 40, "G5", self.GRAY),
            'group_0': (190, 80, 50, 40, "G0", self.GRAY),  # Promiscuous
            'send_1': (260, 80, 50, 40, "S1", self.BLUE),
            
            'send_5': (10, 130, 70, 40, "S5", self.BLUE),
            'send_15': (90, 130, 70, 40, "S15", self.BLUE),
            'receive': (170, 130, 70, 40, "RCV", self.YELLOW),
            'clear': (250, 130, 60, 40, "CLR", self.RED),
            
            'stats': (10, 180, 100, 40, "STATS", self.GREEN),
            'reset': (120, 180, 100, 40, "RESET", self.RED),
            'quit': (230, 180, 80, 40, "QUIT", self.BLACK),
        }
        
        self.setup_display()
    
    def _on_touch_callback(self, x, y):
        """Handle touch events via callback."""
        print(f"Touch at ({x}, {y})")
        # Process button press and check if we should exit
        should_continue = self.handle_button_press(x, y)
        if not should_continue:
            self.exit_requested = True
    
    def setup_display(self):
        """Initialize the display layout."""
        self.display.clear()
        self.display.show_text_at(10, 10, "Network Test", self.WHITE)
        self.display.show_text_at(10, 25, f"MAC: {self.radio.get_my_address()[:12]}...", self.WHITE)
        self.draw_buttons()
        self.update_status()
        self.display_needs_update = False
        self.buttons_need_redraw = False
    
    def draw_buttons(self):
        """Draw all touch buttons."""
        for button_id, (x, y, w, h, label, color) in self.buttons.items():
            # Update group button colors based on current group
            if button_id.startswith('group_'):
                group_num = 0 if button_id == 'group_0' else int(button_id.split('_')[1])
                color = self.GREEN if group_num == self.current_group else self.GRAY
            
            # Draw button background
            self.display.fill_rectangle(x, y, w, h, color)
            self.display.draw_rectangle(x, y, w, h, self.WHITE)
            
            # Draw button label (centered)
            text_x = x + (w - len(label) * 6) // 2
            text_y = y + (h - 8) // 2
            label_color = self.WHITE if color != self.WHITE else self.BLACK
            self.display.show_text_at(text_x, text_y, label, label_color)
        
        self.buttons_need_redraw = False
    
    def update_status(self):
        """Update the diagnostic information display."""
        # Clear status area
        self.display.fill_rectangle(10, 40, 300, 35, self.BLACK)
        
        # Current status
        status_text = f"Group:{self.current_group} Sent:{self.messages_sent} Rcvd:{self.messages_received} Q:{self.queue_count}"
        self.display.show_text_at(10, 42, status_text, self.WHITE)
        
        # Last message info
        if self.last_message:
            msg_display = self.last_message[:30] + "..." if len(self.last_message) > 30 else self.last_message
            self.display.show_text_at(10, 55, f"Last: {msg_display}", self.YELLOW)
        
        # Radio stats
        stats = self.radio.get_stats()
        self.display.show_text_at(10, 68, f"Radio S:{stats['sent']} R:{stats['received']} E:{stats['errors']}", self.GREEN)
        
        self.display_needs_update = False
    
    def handle_button_press(self, x, y):
        """Handle touch button presses."""
        for button_id, (bx, by, bw, bh, label, color) in self.buttons.items():
            if bx <= x <= bx + bw and by <= y <= by + bh:
                return self.handle_button_action(button_id)
        return True  # Continue running
    
    def handle_button_action(self, button_id):
        """Handle specific button actions."""
        print(f"Button pressed: {button_id}")
        
        if button_id.startswith('group_'):
            # Change radio group
            if button_id == 'group_0':
                new_group = 0  # Promiscuous mode
            else:
                new_group = int(button_id.split('_')[1])
            
            self.current_group = new_group
            self.radio.set_group(new_group)
            print(f"Changed to group {new_group}")
            self.buttons_need_redraw = True
            self.display_needs_update = True
            
        elif button_id == 'send_1':
            self.send_test_messages(1)
            
        elif button_id == 'send_5':
            self.send_test_messages(5)
            
        elif button_id == 'send_15':
            self.send_test_messages(15)
            
        elif button_id == 'receive':
            self.manual_receive()
            
        elif button_id == 'clear':
            self.clear_queue()
            
        elif button_id == 'stats':
            self.show_detailed_stats()
            
        elif button_id == 'reset':
            self.reset_counters()
            
        elif button_id == 'quit':
            return False  # Exit program
        
        # Mark display for update after any button action
        self.display_needs_update = True
        return True
    
    def send_test_messages(self, count):
        """Send multiple test messages."""
        print(f"Sending {count} test messages...")
        
        for i in range(count):
            timestamp = get_timestamp()
            message = f"Test{self.messages_sent + 1} T:{timestamp}"
            
            try:
                self.radio.send(message)
                self.messages_sent += 1
                print(f"Sent: {message}")
                
                # Small delay between messages
                if count > 1:
                    delay_ms(50)
                    
            except Exception as e:
                print(f"Send error: {e}")
                break
        
        self.display_needs_update = True
        print(f"Sent {count} messages total")
    
    def manual_receive(self):
        """Manually receive and process messages from queue."""
        received_count = 0
        
        print("Manual receive - draining queue...")
        
        while True:
            message = self.radio.receive(timeout_ms=0)  # Non-blocking
            if message is None:
                break
                
            received_count += 1
            self.messages_received += 1
            self.last_message = message['text']
            self.last_sender = message['sender']
            
            print(f"Received: {message['text']} from {message['sender']} (group {message['group']})")
        
        # Update queue count
        self.queue_count = self.radio.queue_size()
        
        if received_count > 0:
            print(f"Received {received_count} messages from queue")
            self.display_needs_update = True
        else:
            print("No messages in queue")
    
    def clear_queue(self):
        """Clear the message queue."""
        self.radio.clear_queue()
        self.queue_count = 0
        self.last_message = ""
        self.last_sender = ""
        self.display_needs_update = True
        print("Queue cleared")
    
    def show_detailed_stats(self):
        """Show detailed statistics on display."""
        self.display.clear()
        
        # Header
        self.display.show_text_at(10, 10, "DETAILED STATISTICS", self.WHITE)
        
        # Radio stats
        stats = self.radio.get_stats()
        y = 35
        self.display.show_text_at(10, y, f"Radio Sent: {stats['sent']}", self.GREEN)
        y += 15
        self.display.show_text_at(10, y, f"Radio Received: {stats['received']}", self.GREEN)
        y += 15
        self.display.show_text_at(10, y, f"Radio Errors: {stats['errors']}", self.RED)
        y += 15
        
        # Test stats
        self.display.show_text_at(10, y, f"Test Sent: {self.messages_sent}", self.BLUE)
        y += 15
        self.display.show_text_at(10, y, f"Test Received: {self.messages_received}", self.BLUE)
        y += 15
        
        # Current settings
        self.display.show_text_at(10, y, f"Current Group: {self.current_group}", self.YELLOW)
        y += 15
        self.display.show_text_at(10, y, f"Queue Size: {self.queue_count}", self.YELLOW)
        y += 15
        self.display.show_text_at(10, y, f"Channel: {self.radio.get_channel()}", self.YELLOW)
        y += 15
        
        # Device info
        self.display.show_text_at(10, y, f"MAC: {self.radio.get_my_address()}", self.WHITE)
        y += 25
        
        # Last error
        last_error = self.radio.get_last_error()
        if last_error:
            self.display.show_text_at(10, y, "Last Error:", self.RED)
            y += 15
            # Truncate long error messages
            error_display = last_error[:40] + "..." if len(last_error) > 40 else last_error
            self.display.show_text_at(10, y, error_display, self.RED)
        
        # Touch to return
        self.display.show_text_at(10, 220, "Touch screen to return", self.GRAY)
        
        # Wait for touch
        while True:
            touch_data = self.touch.get_touch()
            if touch_data and touch_data['pressed']:
                break
            delay_ms(100)
        
        self.setup_display()
    
    def reset_counters(self):
        """Reset all test counters."""
        self.messages_sent = 0
        self.messages_received = 0
        self.last_message = ""
        self.last_sender = ""
        self.radio.reset_stats()
        self.clear_queue()
        self.display_needs_update = True
        print("All counters reset")
    
    def update_queue_count(self):
        """Update queue count from radio."""
        self.queue_count = self.radio.queue_size()
    
    def check_for_new_messages(self):
        """Check if new messages have arrived and update display if needed."""
        current_queue_size = self.radio.queue_size()
        if current_queue_size != self.last_queue_count:
            self.queue_count = current_queue_size
            self.last_queue_count = current_queue_size
            self.display_needs_update = True
            return True
        return False
    
    def run(self):
        """Main test loop - minimal processing, event-driven updates."""
        print("Network Tester running - use touch interface")
        print("Buttons:")
        print("  G1/G2/G5/G0 - Change radio group (0=promiscuous)")
        print("  S1/S5/S15 - Send 1/5/15 test messages")
        print("  RCV - Manual receive (drain queue)")
        print("  CLR - Clear message queue")
        print("  STATS - Show detailed statistics")
        print("  RESET - Reset all counters")
        print("  QUIT - Exit program")
        
        # Initialize queue count tracking
        self.last_queue_count = self.radio.queue_size()
        last_message_check = 0
        
        while not self.exit_requested:
            current_time = get_timestamp()
            
            # Check for new messages periodically (every 100ms)
            if current_time - last_message_check > 100:
                self.check_for_new_messages()
                last_message_check = current_time
            
            # Only update display when something actually changed
            if self.buttons_need_redraw:
                self.draw_buttons()
            
            if self.display_needs_update:
                self.update_status()
            
            # Minimal delay to prevent excessive CPU usage
            delay_ms(10)
        
        print("Network Tester exiting...")
        self.display.clear()
        self.display.show_text_at(100, 120, "Test Complete", self.WHITE)


def main():
    """Main program entry point."""
    try:
        tester = NetworkTester()
        tester.run()
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        
    except Exception as e:
        print(f"Error: {e}")
        # Try to show error on display if possible
        try:
            display = Display()
            display.clear()
            display.show_text_at(10, 100, "Error occurred:", "red")
            display.show_text_at(10, 120, str(e)[:30], "red")
        except Exception:
            pass
    
    finally:
        print("Cleaning up...")


if __name__ == "__main__":
    main()
