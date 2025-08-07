"""
Easy Display Library Demo
Comprehensive demonstration of all easy_display functionality.

This script demonstrates:
- Basic text display and positioning
- Shape drawing (rectangles, circles, ellipses, polygons)
- Color handling (strings, RGB tuples, hex values)
- Performance optimization features
- Buffered drawing operations
- Complex drawing scenarios that test performance

Usage:
- Copy to boot.py on ESP32 device, or
- Import and run directly: import display_demo
"""

from easy_display import Display, init, show_text, clear, draw_circle, draw_rectangle
from easy_display import draw_line, draw_pixel, draw_ellipse, draw_polygon
from easy_display import begin_drawing, end_drawing, display_on, display_off, display_sleep
import time
import gc

def demo_basic_text():
    """Demo basic text display functionality."""
    print("=== Basic Text Display Demo ===")
    
    # Create display instance
    display = Display()
    
    # Simple text display
    display.show_text("Hello, ESP32 World!")
    time.sleep(2)
    
    # Text with colors
    display.show_text("Colored text demo", color="red", background="blue")
    time.sleep(2)
    
    # Multi-line text
    multi_line = ["Line 1: Basic text in lists is displayed over multiple lines",
                "Line 2: Automatic wrapping for really long lines is supported for regular text drawing!",
                "Line 3: Multiple colors supported",
                "Line 4: Easy to use!"]
    display.show_text(multi_line, color="yellow", background="black")
    time.sleep(3)
    
    # Text at specific positions
    display.clear("navy")
    display.show_text_at(10, 10, "Top Left", "white")
    display.show_text_at(200, 10, "Top Right", "green")
    display.show_text_at(10, 200, "Bottom Left", "red")
    display.show_text_at(180, 200, "Bottom Right", "cyan")
    display.show_text_at(120, 100, "CENTER", "yellow")
    time.sleep(3)

def demo_convenience_functions():
    """Demo convenience functions for simple usage."""
    print("=== Convenience Functions Demo ===")
    
    # Initialize default display
    init()
    
    # Use convenience functions (no need to create Display instance)
    show_text("Using convenience functions!", "white", "purple")
    time.sleep(2)
    
    clear("black")
    draw_circle(160, 120, 80, "red", filled=True)
    draw_circle(160, 120, 60, "yellow", filled=True)
    draw_circle(160, 120, 40, "green", filled=True)
    draw_circle(160, 120, 20, "blue", filled=True)
    time.sleep(3)

def demo_color_handling():
    """Demo different color specification methods."""
    print("=== Color Handling Demo ===")
    
    display = Display()
    
    # String colors
    display.clear("black")
    colors = ["red", "green", "blue", "yellow", "cyan", "magenta", "white", "orange", "purple", "pink"]
    for i, color in enumerate(colors):
        x = (i % 5) * 60 + 20
        y = (i // 5) * 60 + 50
        display.fill_rectangle(x, y, 50, 40, color)
        display.show_text_at(x + 5, y + 15, color[:3], "black")
    time.sleep(4)
    
    # RGB tuple colors
    display.clear("black")
    display.show_text_at(10, 10, "RGB Color Demo", "white")
    
    # Rainbow using RGB values
    for i in range(100):
        r = int(255 * (1 + abs(2 * i / 100 - 1)) / 2)
        g = int(255 * (1 - abs(2 * i / 100 - 1)))
        b = int(255 * (1 - abs(2 * i / 100 - 1)) if i < 50 else 255 * abs(2 * i / 100 - 1))
        display.draw_line(i * 3, 50, i * 3, 150, (r, g, b))
    time.sleep(3)

def demo_basic_shapes():
    """Demo basic shape drawing."""
    print("=== Basic Shapes Demo ===")
    
    display = Display()
    
    # Rectangles
    display.clear("black")
    display.show_text_at(10, 10, "Rectangle Demo", "white")
    
    # Outline rectangles
    display.draw_rectangle(50, 50, 80, 60, "red")
    display.draw_rectangle(150, 50, 80, 60, "green")
    
    # Filled rectangles
    display.draw_rectangle(50, 130, 80, 60, "blue", filled=True)
    display.draw_rectangle(150, 130, 80, 60, "yellow", filled=True)
    time.sleep(3)
    
    # Circles
    display.clear("black")
    display.show_text_at(10, 10, "Circle Demo", "white")
    
    # Different sized circles
    for i in range(5):
        radius = 15 + i * 10
        x = 60 + i * 50
        y = 120
        color = ["red", "green", "blue", "yellow", "cyan"][i]
        display.draw_circle(x, y, radius, color)
    time.sleep(2)
    
    # Filled circles
    display.clear("navy")
    for i in range(4):
        radius = 20 + i * 15
        x = 80 + i * 60
        y = 120
        color = ["orange", "purple", "pink", "lime"][i]
        display.draw_circle(x, y, radius, color, filled=True)
    time.sleep(3)

def demo_advanced_shapes():
    """Demo advanced shape drawing (ellipses, polygons)."""
    print("=== Advanced Shapes Demo ===")
    
    display = Display()
    
    # Ellipses
    display.clear("black")
    display.show_text_at(10, 10, "Ellipse Demo", "white")
    
    # Various ellipse sizes and orientations
    display.draw_ellipse(80, 80, 100, 60, "red")  # Wide ellipse
    display.draw_ellipse(240, 80, 60, 100, "green")  # Tall ellipse
    display.draw_ellipse(160, 160, 120, 80, "blue", filled=True)  # Filled ellipse
    time.sleep(3)
    
    # Polygons
    display.clear("black")
    display.show_text_at(10, 10, "Polygon Demo", "white")
    
    # Triangle
    triangle = [(160, 50), (120, 120), (200, 120)]
    display.draw_polygon(triangle, "red")
    
    # Pentagon
    import math
    pentagon = []
    for i in range(5):
        angle = i * 2 * math.pi / 5 - math.pi / 2
        x = int(80 + 40 * math.cos(angle))
        y = int(180 + 40 * math.sin(angle))
        pentagon.append((x, y))
    display.draw_polygon(pentagon, "green", filled=True)
    
    # Hexagon
    hexagon = []
    for i in range(6):
        angle = i * 2 * math.pi / 6
        x = int(240 + 35 * math.cos(angle))
        y = int(180 + 35 * math.sin(angle))
        hexagon.append((x, y))
    display.draw_polygon(hexagon, "blue")
    time.sleep(4)

def demo_lines_and_pixels():
    """Demo line and pixel drawing."""
    print("=== Lines and Pixels Demo ===")
    
    display = Display()
    
    # Line patterns
    display.clear("black")
    display.show_text_at(10, 10, "Line Patterns", "white")
    
    # Grid pattern
    for i in range(0, 320, 20):
        display.draw_line(i, 30, i, 240, "gray")
    for i in range(30, 240, 20):
        display.draw_line(0, i, 320, i, "gray")
    
    # Diagonal lines
    for i in range(0, 300, 15):
        display.draw_line(i, 30, i + 100, 200, "yellow")
        display.draw_line(320 - i, 30, 220 - i, 200, "cyan")
    time.sleep(3)
    
    # Pixel art demo
    display.clear("black")
    display.show_text_at(10, 10, "Pixel Art Demo", "white")
    
    # Draw a simple smiley face with pixels
    center_x, center_y = 160, 120
    
    # Face outline (circle of pixels)
    import math
    for angle in range(0, 360, 2):
        rad = math.radians(angle)
        x = int(center_x + 50 * math.cos(rad))
        y = int(center_y + 50 * math.sin(rad))
        display.draw_pixel(x, y, "yellow")
    
    # Eyes (changed from black to white so they're visible on black background)
    for dx in [-20, 20]:
        for dy in range(-5, 6):
            for dx2 in range(-3, 4):
                display.draw_pixel(center_x + dx + dx2, center_y - 20 + dy, "white")
    
    # Smile (changed from black to red so it's visible on black background)
    for angle in range(30, 151, 2):
        rad = math.radians(angle)
        x = int(center_x + 25 * math.cos(rad))
        y = int(center_y + 25 * math.sin(rad))
        display.draw_pixel(x, y, "red")
    
    time.sleep(4)

def demo_performance_unbuffered():
    """Demo performance without buffering (slower)."""
    print("=== Performance Demo: Unbuffered Drawing ===")
    
    display = Display()
    display.clear("black")
    display.show_text_at(10, 10, "Unbuffered: Drawing 1000 pixels...", "white")
    
    start_time = time.ticks_ms()
    
    # Draw many individual pixels (inefficient without buffering)
    import random
    for i in range(1000):
        x = random.randint(0, 319)
        y = random.randint(30, 239)
        color = random.choice(["red", "green", "blue", "yellow", "cyan", "magenta"])
        display.draw_pixel(x, y, color)
    
    end_time = time.ticks_ms()
    duration = time.ticks_diff(end_time, start_time)
    
    display.show_text_at(10, 220, f"Unbuffered: {duration}ms", "white")
    print(f"Unbuffered drawing took: {duration}ms")
    time.sleep(3)

def demo_performance_buffered():
    """Demo performance with buffering (faster)."""
    print("=== Performance Demo: Buffered Drawing ===")
    
    display = Display()
    display.clear("black")
    display.show_text_at(10, 10, "Buffered: Drawing 1000 pixels...", "white")
    
    start_time = time.ticks_ms()
    
    # Use buffered drawing for better performance
    display.begin_drawing()
    
    import random
    for i in range(1000):
        x = random.randint(0, 319)
        y = random.randint(30, 239)
        color = random.choice(["red", "green", "blue", "yellow", "cyan", "magenta"])
        display.draw_pixel(x, y, color)
    
    display.end_drawing()  # Flush all pixels at once
    
    end_time = time.ticks_ms()
    duration = time.ticks_diff(end_time, start_time)
    
    display.show_text_at(10, 220, f"Buffered: {duration}ms", "white")
    print(f"Buffered drawing took: {duration}ms")
    time.sleep(3)

def demo_complex_scene():
    """Demo complex scene with multiple elements."""
    print("=== Complex Scene Demo ===")
    
    display = Display()
    
    # Complex animated scene
    display.clear("navy")
    display.show_text_at(10, 10, "Complex Scene Demo", "white")
    
    # Background elements
    display.fill_rectangle(0, 200, 320, 40, "green")  # Ground
    display.draw_circle(280, 40, 25, "yellow", filled=True)  # Sun
    
    # Buildings
    buildings = [
        (50, 120, 40, 80, "gray"),
        (100, 100, 35, 100, "darkgray"),
        (145, 130, 45, 70, "lightgray"),
        (200, 110, 50, 90, "gray"),
        (260, 140, 30, 60, "darkgray")
    ]
    
    for x, y, w, h, color in buildings:
        display.fill_rectangle(x, y, w, h, color)
        # Windows
        for wy in range(y + 10, y + h - 10, 15):
            for wx in range(x + 5, x + w - 5, 10):
                if (wx + wy) % 30 < 15:  # Some windows lit
                    display.fill_rectangle(wx, wy, 6, 8, "yellow")
                else:
                    display.fill_rectangle(wx, wy, 6, 8, "black")
    
    # Clouds
    cloud_positions = [(80, 60), (180, 50), (250, 70)]
    for cx, cy in cloud_positions:
        display.draw_circle(cx, cy, 20, "grey", filled=True)
        display.draw_circle(cx + 15, cy, 15, "grey", filled=True)
        display.draw_circle(cx - 15, cy + 5, 12, "grey", filled=True)
    
    time.sleep(4)

def demo_memory_stress_test():
    """Demo memory usage with large operations."""
    print("=== Memory Stress Test ===")
    
    display = Display()
    
    # Show initial memory
    gc.collect()
    initial_free = gc.mem_free()
    print(f"Initial free memory: {initial_free} bytes")
    
    display.clear("black")
    display.show_text_at(10, 10, f"Free RAM: {initial_free//1024}KB", "white")
    
    # Large filled shapes (tests memory efficiency)
    display.show_text_at(10, 30, "Drawing large shapes...", "yellow")
    
    # Large rectangles
    for i in range(5):
        x = i * 60
        y = 60
        w = 50
        h = 100
        color = ["red", "green", "blue", "yellow", "cyan"][i]
        display.fill_rectangle(x, y, w, h, color)
    
    # Check memory after large operations
    gc.collect()
    after_shapes = gc.mem_free()
    print(f"Memory after shapes: {after_shapes} bytes")
    
    # Large circle
    display.fill_circle(160, 160, 70, "purple")
    
    # Memory after circle
    gc.collect()
    final_free = gc.mem_free()
    print(f"Final free memory: {final_free} bytes")
    
    display.show_text_at(10, 220, f"Final RAM: {final_free//1024}KB", "white")
    
    memory_used = initial_free - final_free
    print(f"Memory used by operations: {memory_used} bytes")
    
    time.sleep(3)

def demo_display_control():
    """Demo display power and sleep control."""
    print("=== Display Control Demo ===")
    
    display = Display()
    
    # Normal operation
    display.clear("black")
    display.show_text_at(10, 100, "Display Control Demo", "white", "black")
    display.show_text_at(10, 120, "Display will turn off in 3 seconds", "yellow")
    time.sleep(3)
    
    # Turn display off
    print("Turning display off...")
    display.display_off()
    time.sleep(2)
    
    # Turn display back on
    print("Turning display on...")
    display.display_on()
    display.show_text_at(10, 140, "Display is back on!", "green")
    time.sleep(2)
    
    # Sleep mode test
    display.show_text_at(10, 160, "Entering sleep mode...", "red")
    time.sleep(2)
    print("Entering sleep mode...")
    display.sleep(True)
    time.sleep(2)
    
    # Wake up
    print("Waking up from sleep...")
    display.sleep(False)
    display.show_text_at(10, 180, "Awake from sleep!", "cyan")
    time.sleep(2)

def demo_error_handling():
    """Demo error handling and edge cases."""
    print("=== Error Handling Demo ===")
    
    display = Display()
    display.clear("black")
    display.show_text_at(10, 10, "Error Handling Demo", "white")
    
    # Test drawing outside bounds (should be clipped gracefully)
    display.show_text_at(10, 30, "Drawing outside bounds (clipped):", "yellow")
    
    # Rectangle partially off-screen
    display.draw_rectangle(-20, 60, 100, 50, "red", filled=True)
    display.draw_rectangle(270, 60, 100, 50, "green", filled=True)
    display.draw_rectangle(100, -10, 50, 50, "blue", filled=True)
    display.draw_rectangle(100, 220, 50, 50, "cyan", filled=True)
    
    # Circles off-screen
    display.draw_circle(-30, 150, 40, "purple", filled=True)
    display.draw_circle(350, 150, 40, "orange", filled=True)
    
    # Invalid color (should default to white)
    display.show_text_at(10, 180, "Invalid color test:", "white")
    display.draw_rectangle(10, 200, 50, 30, "invalidcolor", filled=True)
    
    # Zero-size shapes (should be handled gracefully)
    try:
        display.draw_rectangle(200, 200, 0, 20, "red")  # Zero width
        display.show_text_at(150, 180, "Zero-size shapes handled", "green")
    except ValueError as e:
        display.show_text_at(150, 180, f"Error caught: {str(e)[:20]}", "red")
    
    time.sleep(4)

def benchmark_drawing_methods():
    """Benchmark different drawing methods."""
    print("=== Drawing Method Benchmarks ===")
    
    display = Display()
    
    tests = [
        ("100 pixels", lambda: [display.draw_pixel(i, 100, "red") for i in range(100)]),
        ("50 lines", lambda: [display.draw_line(i*4, 50, i*4+20, 80, "green") for i in range(50)]),
        ("20 rectangles", lambda: [display.draw_rectangle(i*15, 120, 10, 20, "blue", filled=True) for i in range(20)]),
        ("10 circles", lambda: [display.draw_circle(i*30+20, 180, 10, "yellow", filled=True) for i in range(10)]),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        display.clear("black")
        display.show_text_at(10, 10, f"Benchmarking: {test_name}", "white")
        
        # Run the benchmark and time it
        start_time = time.ticks_ms()
        test_func()
        end_time = time.ticks_ms()
        
        duration = time.ticks_diff(end_time, start_time)
        results.append((test_name, duration))
        
        display.show_text_at(10, 220, f"{test_name}: {duration}ms", "cyan")
        print(f"{test_name}: {duration}ms")
        time.sleep(2)
    
    # Show summary
    display.clear("black")
    display.show_text_at(10, 10, "Benchmark Results:", "white")
    for i, (name, duration) in enumerate(results):
        display.show_text_at(10, 30 + i*20, f"{name}: {duration}ms", "yellow")
    time.sleep(5)

def run_all_demos():
    """Run all demonstration functions."""
    print("Starting Easy Display Library Demo Suite...")
    print("This demo will run for approximately 2-3 minutes.")
    
    demos = [
        demo_basic_text,
        demo_convenience_functions,
        demo_color_handling,
        demo_basic_shapes,
        demo_advanced_shapes,
        demo_lines_and_pixels,
        demo_performance_unbuffered,
        demo_performance_buffered,
        demo_complex_scene,
        demo_memory_stress_test,
        demo_display_control,
        demo_error_handling,
        benchmark_drawing_methods
    ]
    
    for i, demo in enumerate(demos, 1):
        print(f"\n--- Running Demo {i}/{len(demos)}: {demo.__name__} ---")
        try:
            demo()
        except Exception as e:
            print(f"Demo {demo.__name__} failed with error: {e}")
            # Continue with next demo
        
        # Small pause between demos
        time.sleep(1)
    
    # Final message
    display = Display()
    display.clear("black")
    display.show_text([
        "Easy Display Demo Complete!",
        "",
        "All features demonstrated:",
        "- Text display & positioning",
        "- Shape drawing & filling", 
        "- Color handling (string/RGB)",
        "- Performance optimization",
        "- Buffered drawing",
        "- Memory management",
        "- Error handling",
        "- Display control",
        "",
        "Library is ready for use!"
    ], "green", "black")
    
    print("\n=== Demo Suite Complete ===")
    print("Easy Display Library demonstration finished!")
    print("All features have been tested and demonstrated.")

# Run the demo suite when this file is imported or executed
print("Easy Display Library Demo Starting...")
run_all_demos()
