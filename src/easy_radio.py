"""
Easy Radio Library for ESP32 with ESP-NOW
A student-friendly wireless communication library using ESP-NOW broadcast mode.

This library simplifies ESP-NOW communication for students by providing:
- Simple send/receive functions with automatic background message queuing
- Group-based message filtering (like micro:bit radio groups)
- Message queuing to prevent lost messages (handled automatically via callbacks)
- Automatic peer management with RSSI
- Channel configuration support with minimal interruption
- WiFi TX power control for range adjustment
- No async code required - messages arrive automatically in background

Example usage:
    from easy_radio import Radio
    
    # Create radio instance with custom settings
    radio = Radio(channel=6, queue_size=20, tx_power=10, group=5)
    
    # Send a message (only group 5 radios will receive it)
    radio.send("Hello World!")
    
    # Check for received messages (automatically filtered by group)
    message = radio.receive()
    if message:
        print(f"From {message['sender']}: {message['text']} (group: {message['group']})")
    
    # Change to promiscuous mode (receive all groups)
    radio.set_group(0)
    
    # Or change to a specific group
    radio.set_group(12)
    
    # Get all queued messages at once
    messages = radio.receive_all()
    for msg in messages:
        print(f"Group {msg['group']}: {msg['text']}")

Convenience functions for simple usage:
    import easy_radio
    
    # Default is group 1
    easy_radio.send("Test message")
    msg = easy_radio.receive(timeout_ms=500)
    
    # Change group at runtime
    easy_radio.set_group(7)  # Join group 7
    easy_radio.set_group(0)  # Promiscuous mode
"""

import network
import espnow
from time import ticks_ms


class Radio:
    """Simple ESP-NOW radio interface for students."""
    
    def __init__(self, channel=None, queue_size=10, tx_power=None, group=1):
        """Initialize the radio.
        
        Args:
            channel (int, optional): WiFi channel to use (1-13). If None, uses default.
            queue_size (int): Maximum number of messages to queue (default: 10)
            tx_power (int, optional): WiFi TX power in dBm (1-13, affects ESP-NOW range
            and maps to the internal 8-20 dBm power range)
            group (int): Radio group (1-255). Use 0 for promiscuous mode (receive all groups)
        """
        self._espnow = None
        self._wlan = None
        self._channel = channel
        self._tx_power = tx_power
        self._group = group
        self._stats = {
            'sent': 0,
            'received': 0,
            'errors': 0
        }
        self._peer_rssi = {}  # Store RSSI for each peer
        self._last_error = None
        
        # Message queue for buffering received messages
        self._message_queue = []
        self._max_queue_size = queue_size
        
        # Validate group
        if not (0 <= group <= 255):
            raise ValueError("Group must be between 0 (promiscuous) and 255")
        
        # Initialize the radio
        self._init_radio()
    
    def _init_radio(self):
        """Initialize the ESP-NOW radio interface."""
        try:
            # Set up WiFi in station mode (required for ESP-NOW)
            self._wlan = network.WLAN(network.STA_IF)
            self._wlan.active(True)
            
            # Set channel if specified
            if self._channel is not None:
                if 1 <= self._channel <= 13:
                    self._wlan.config(channel=self._channel)
                else:
                    raise ValueError("Channel must be between 1 and 13")
            
            # Set TX power if specified
            if self._tx_power is not None:
                if 1 <= self._tx_power <= 13:
                    self._wlan.config(txpower=self._tx_power + 7)  # Maps to internal 8-20 dBm range
                else:
                    raise ValueError("TX power must be between 1 and 13 dBm")
            
            # Disconnect from any WiFi networks (ESP-NOW works without connection)
            self._wlan.disconnect()
            
            # Initialize ESP-NOW
            self._espnow = espnow.ESPNow()
            self._espnow.active(True)
            
            # Set up interrupt callback for automatic message queuing
            # Use irq() method as per MicroPython documentation
            self._espnow.irq(self._on_message_received)
            
            # Add broadcast peer for sending to all devices
            broadcast_mac = b'\xff\xff\xff\xff\xff\xff'
            try:
                self._espnow.add_peer(broadcast_mac)
            except OSError:
                # Peer might already exist, that's OK
                pass
            
        except Exception as e:
            self._last_error = f"Failed to initialize radio: {e}"
            raise RuntimeError(self._last_error)
    
    def _on_message_received(self, espnow_instance):
        """Background callback when ESP-NOW message arrives.
        
        This runs automatically when messages are received and adds them
        to the queue for later retrieval via receive(). Messages are filtered
        by group unless in promiscuous mode (group 0).
        
        Args:
            espnow_instance: The ESP-NOW instance that triggered the interrupt
        """
        try:
            # Read all available messages
            while True:
                mac, msg = espnow_instance.irecv(0)
                if mac is None:
                    break  # No more messages
                
                # Parse message header: [group][length][message...]
                if len(msg) < 2:
                    continue  # Invalid message - too short for header
                
                msg_group = msg[0]
                msg_length = msg[1]
                
                # Check if message length is valid
                if len(msg) < (2 + msg_length):
                    continue  # Invalid message - length mismatch
                
                # Filter by group (unless we're in promiscuous mode)
                if self._group != 0 and msg_group != self._group:
                    continue  # Not our group, ignore
                
                # Extract actual message content
                message_bytes = msg[2:(2 + msg_length)]
                
                # Decode message
                try:
                    text = message_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    text = str(message_bytes)
                
                # Format MAC address
                sender = ':'.join('%02x' % b for b in mac)
                
                # Get RSSI (may not be reliable)
                rssi = self._get_peer_rssi(mac)
                
                # Create message info with group information
                message_info = {
                    'sender': sender,
                    'text': text,
                    'rssi': rssi,
                    'time': ticks_ms(),
                    'group': msg_group  # Include original group
                }
                
                # Add to queue (this handles overflow automatically)
                self.queue_message(message_info)
                
                # Update stats
                self._stats['received'] += 1
                
        except Exception as e:
            self._stats['errors'] += 1
            self._last_error = f"Message callback error: {e}"
    
    def send(self, message):
        """Send a message to all nearby radios in the same group.
        
        Args:
            message (str): The message to send (max 248 characters due to group header)
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not isinstance(message, str):
            message = str(message)
        
        # Limit message length (reserve 2 bytes for group header)
        if len(message) > 248:
            message = message[:248]
        
        try:
            # Create message with group header
            # Format: [group_byte][length_byte][message_bytes]
            msg_bytes = message.encode('utf-8')
            header = bytes([self._group, len(msg_bytes)])
            full_message = header + msg_bytes
            
            # Send to broadcast address
            broadcast_mac = b'\xff\xff\xff\xff\xff\xff'
            self._espnow.send(broadcast_mac, full_message, True)
            self._stats['sent'] += 1
                
        except Exception as e:
            self._stats['errors'] += 1
            self._last_error = f"Send error: {e}"
    
    def receive(self, timeout_ms=0):
        """Check for received messages from the queue.
        
        Messages are automatically queued by the background callback when they arrive.
        
        Args:
            timeout_ms (int): How long to wait for a message in milliseconds.
                            0 = don't wait, just check once
                            
        Returns:
            dict or None: Message info with keys 'sender', 'text', 'rssi', 'time'
                         Returns None if no message received
        """
        # Check if we have queued messages
        if self._message_queue:
            return self._message_queue.pop(0)
        
        # If no messages and timeout is 0, return immediately
        if timeout_ms == 0:
            return None
        
        # Wait for a message to arrive (polling the queue)
        start_time = ticks_ms()
        
        while True:
            # Check queue again
            if self._message_queue:
                return self._message_queue.pop(0)
            
            # Check if timeout exceeded
            elapsed = ticks_ms() - start_time
            if elapsed >= timeout_ms:
                return None
            
            # Small delay to prevent busy waiting
            try:
                # MicroPython
                import time
                time.sleep_ms(min(10, timeout_ms - elapsed))
            except (ImportError, AttributeError):
                # Standard Python fallback
                import time
                time.sleep(min(0.01, (timeout_ms - elapsed) / 1000.0))
            
        return None
    
    def _get_peer_rssi(self, mac_addr):
        """Get RSSI for a peer (signal strength)."""
        try:
            # Try to get RSSI from peers table
            peer = self._espnow.peers_table.get(mac_addr, [-100, 0])
            rssi = peer[0]
            
            # If not found in peers, add them and return default
            try:
                self._espnow.add_peer(mac_addr)
            except OSError:
                pass
            return rssi
                
        except Exception:
            return -100  # Default when RSSI unavailable
    
    def get_my_address(self):
        """Get this device's MAC address.
        
        Returns:
            str: MAC address in format "aa:bb:cc:dd:ee:ff"
        """
        if self._wlan:
            mac = self._wlan.config('mac')
            return ':'.join('%02x' % b for b in mac)
        return "unknown"
    
    def get_channel(self):
        """Get the current WiFi channel.
        
        Returns:
            int: Channel number (1-13)
        """
        if self._wlan:
            return self._wlan.config('channel')
        return 0
    
    def get_stats(self):
        """Get radio statistics.
        
        Returns:
            dict: Statistics with keys 'sent', 'received', 'errors'
        """
        return self._stats.copy()
    
    def get_last_error(self):
        """Get the last error message.
        
        Returns:
            str or None: Last error message, or None if no errors
        """
        return self._last_error
    
    def reset_stats(self):
        """Reset all statistics counters."""
        self._stats = {
            'sent': 0,
            'received': 0,
            'errors': 0
        }
        self._last_error = None
    
    def receive_all(self):
        """Get all queued messages at once.
        
        Returns:
            list: List of message dictionaries, empty list if no messages
        """
        messages = self._message_queue.copy()
        self._message_queue.clear()
        return messages
    
    def queue_message(self, message_info):
        """Add a message to the queue (internal method for background receiving).
        
        Args:
            message_info (dict): Message information dictionary
        """
        # Add to queue, removing oldest if at capacity
        if len(self._message_queue) >= self._max_queue_size:
            self._message_queue.pop(0)  # Remove oldest
        self._message_queue.append(message_info)
    
    def clear_queue(self):
        """Clear all queued messages."""
        self._message_queue.clear()
    
    def queue_size(self):
        """Get current number of queued messages.
        
        Returns:
            int: Number of messages in queue
        """
        return len(self._message_queue)
    
    def set_channel(self, channel):
        """Change the WiFi channel with minimal interruption.
        
        Args:
            channel (int): Channel number (1-13)
            
        Note: This will clear the message queue to prevent confusion
              about which channel messages were received on.
        """
        if not (1 <= channel <= 13):
            raise ValueError("Channel must be between 1 and 13")
        
        if self._channel == channel:
            return  # No change needed
        
        old_channel = self._channel
        self._channel = channel
        
        try:
            # Clear message queue to avoid confusion
            self.clear_queue()
            
            # Quick channel change without full reinitialization if possible
            if self._wlan and self._wlan.active():
                self._wlan.config(channel=channel)
            else:
                # Full reinitialize if WiFi is not active
                self.close()
                self._init_radio()
                
        except Exception as e:
            # If channel change fails, revert and raise error
            self._channel = old_channel
            self._last_error = f"Channel change failed: {e}"
            raise RuntimeError(self._last_error)
    
    def set_power(self, tx_power):
        """Change the WiFi TX power with minimal interruption.
        
        Args:
            tx_power (int): TX power level (1-13, maps to internal 8-20 dBm range)
            
        Note: This affects ESP-NOW transmission range. Higher values = longer range
              but more power consumption.
        """
        if not (1 <= tx_power <= 13):
            raise ValueError("TX power must be between 1 and 13 dBm")
        
        if self._tx_power == tx_power:
            return  # No change needed
        
        old_power = self._tx_power
        self._tx_power = tx_power
        
        try:
            # Change power without full reinitialization if possible
            if self._wlan and self._wlan.active():
                self._wlan.config(txpower=tx_power + 7)  # Maps to internal 8-20 dBm range
            else:
                # Full reinitialize if WiFi is not active
                self.close()
                self._init_radio()
                
        except Exception as e:
            # If power change fails, revert and raise error
            self._tx_power = old_power
            self._last_error = f"Power change failed: {e}"
            raise RuntimeError(self._last_error)
    
    def get_power(self):
        """Get the current WiFi TX power setting.
        
        Returns:
            int: Current TX power level (1-13), or None if not set
        """
        return self._tx_power
    
    def set_group(self, group):
        """Change the radio group for message filtering.
        
        Args:
            group (int): Group number (1-255) or 0 for promiscuous mode
            
        Note: Only affects message filtering, no radio reinitialization needed
        """
        if not (0 <= group <= 255):
            raise ValueError("Group must be between 0 (promiscuous) and 255")
        
        self._group = group
    
    def get_group(self):
        """Get the current radio group.
        
        Returns:
            int: Current group (0=promiscuous, 1-255=group number)
        """
        return self._group
    
    def close(self):
        """Close the radio and free resources."""
        if self._espnow:
            try:
                self._espnow.active(False)
            except Exception:
                pass
            self._espnow = None
        
        if self._wlan:
            try:
                self._wlan.active(False)
            except Exception:
                pass
            self._wlan = None


# Convenience functions for even simpler usage
_default_radio = None

def init(channel=None):
    """Initialize the default radio instance.
    
    Args:
        channel (int, optional): WiFi channel to use (1-13)
    """
    global _default_radio
    _default_radio = Radio(channel=channel)

def send(message):
    """Send a message using the default radio.
    
    Args:
        message (str): Message to send
        
    Returns:
        bool: True if sent successfully
    """
    if _default_radio is None:
        init()
    return _default_radio.send(message)

def receive(timeout_ms=0):
    """Receive a message using the default radio.
    
    Args:
        timeout_ms (int): Timeout in milliseconds
        
    Returns:
        dict or None: Message info or None
    """
    if _default_radio is None:
        init()
    return _default_radio.receive(timeout_ms)

def my_address():
    """Get this device's MAC address.
    
    Returns:
        str: MAC address
    """
    if _default_radio is None:
        init()
    return _default_radio.get_my_address()

def stats():
    """Get radio statistics.
    
    Returns:
        dict: Statistics
    """
    if _default_radio is None:
        init()
    return _default_radio.get_stats()

def receive_all():
    """Get all queued messages using the default radio.
    
    Returns:
        list: List of message dictionaries
    """
    if _default_radio is None:
        init()
    return _default_radio.receive_all()

def clear_queue():
    """Clear all queued messages using the default radio."""
    if _default_radio is None:
        init()
    return _default_radio.clear_queue()

def queue_size():
    """Get number of queued messages using the default radio.
    
    Returns:
        int: Number of messages in queue
    """
    if _default_radio is None:
        init()
    return _default_radio.queue_size()

def set_channel(channel):
    """Change channel using the default radio.
    
    Args:
        channel (int): Channel number (1-13)
    """
    if _default_radio is None:
        init()
    return _default_radio.set_channel(channel)

def set_power(tx_power):
    """Change TX power using the default radio.
    
    Args:
        tx_power (int): TX power level (1-13)
    """
    if _default_radio is None:
        init()
    return _default_radio.set_power(tx_power)

def get_power():
    """Get current TX power using the default radio.
    
    Returns:
        int: Current TX power level (1-13), or None if not set
    """
    if _default_radio is None:
        init()
    return _default_radio.get_power()

def set_group(group):
    """Change group using the default radio.
    
    Args:
        group (int): Group number (0=promiscuous, 1-255=group)
    """
    if _default_radio is None:
        init()
    return _default_radio.set_group(group)

def get_group():
    """Get current group using the default radio.
    
    Returns:
        int: Current group (0=promiscuous, 1-255=group number)
    """
    if _default_radio is None:
        init()
    return _default_radio.get_group()

