import socket
import pigpio
import time
import threading

# Idle blinking variables
last_blink_time = {}
led_blink_state = {}
active_beeps = {}  # Track active beep threads

# Initialize pigpio
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio daemon.")
    exit()

# GPIO Pin Setup for servos, LEDs, and buzzers
servo_pins = {
    1: {"horizontal": 17, "vertical": 18},  # Camera 1 pins
    2: {"horizontal": 22, "vertical": 23},  # Camera 2 pins
}

led_pins = {
    1: {"red": 24, "green": 25},  # Camera 1 LEDs
    2: {"red": 27, "green": 4},  # Camera 2 LEDs
}

buzzer_pins = {
    1: 5,  # Camera 1 buzzer
    2: 6,  # Camera 2 buzzer
}

# Define PWM frequency and initial position (middle)
PWM_FREQ = 50
INITIAL_POSITION = 1650  # Default position for servos

# Initialize servos
for cam_id, pins in servo_pins.items():
    for pin in pins.values():
        pi.set_mode(pin, pigpio.OUTPUT)
        pi.set_servo_pulsewidth(pin, INITIAL_POSITION)

# Initialize LEDs and buzzers
for cam_id, leds in led_pins.items():
    for pin in leds.values():
        pi.set_mode(pin, pigpio.OUTPUT)
        pi.write(pin, 0)  # Turn off LEDs initially
    pi.set_mode(buzzer_pins[cam_id], pigpio.OUTPUT)
    pi.write(buzzer_pins[cam_id], 0)  # Turn off buzzers initially

    # Initialize idle state variables
    last_blink_time[cam_id] = time.time()
    led_blink_state[cam_id] = False

def set_angle(pin, angle):
    """Convert angle to pulse width and set servo position."""
    pulsewidth = 900 + (angle / 180) * 1500  # Convert angle to pulse width (900 to 2400 us)
    pi.set_servo_pulsewidth(pin, pulsewidth)

def indicate_action(cam_id):
    """Indicate action with LEDs and buzzer."""
    pi.write(led_pins[1]["red"], 0)  # Turn off red LED
    pi.write(led_pins[2]["red"], 0)  # Turn off red LED
    pi.write(led_pins[cam_id]["green"], 1)  # Turn on green LED
    pi.write(buzzer_pins[cam_id], 1)  # Turn on buzzer
    time.sleep(0.05)  # Beep for 50 ms
    pi.write(buzzer_pins[cam_id], 0)  # Turn off buzzer

def non_blocking_beep(cam_id, duration):
    """Trigger a non-blocking long beep."""
    if cam_id in active_beeps:
        print(f"Camera {cam_id} is already beeping.")
        return

    def beep_worker():
        """Thread worker for non-blocking beep."""
        pi.write(buzzer_pins[cam_id], 1)  # Turn on buzzer
        pi.write(led_pins[cam_id]["green"], 0)
        pi.write(led_pins[cam_id]["red"], 1)
        time.sleep(duration)  # Beep for specified duration
        pi.write(buzzer_pins[cam_id], 0)  # Turn off buzzer
        del active_beeps[cam_id]  # Remove from active beeps when done

    active_beeps[cam_id] = threading.Thread(target=beep_worker)
    active_beeps[cam_id].start()

def blink_idle_red():
    """Blink red LEDs for all cameras in idle state."""
    pi.write(led_pins[1]["green"], 0)
    pi.write(led_pins[2]["green"], 0)
    current_time = time.time()
    for cam_id in led_pins.keys():
        if current_time - last_blink_time[cam_id] > 0.5:  # Toggle every 0.5 seconds
            last_blink_time[cam_id] = current_time
            led_blink_state[cam_id] = not led_blink_state[cam_id]
            pi.write(led_pins[cam_id]["red"], int(led_blink_state[cam_id]))
            pi.write(led_pins[cam_id]["green"], int(led_blink_state[cam_id]))

# Network Setup
host = '0.0.0.0'
port = 5000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)
print("Waiting for connections...")

try:
    while True:
        # Idle state: Blink red LEDs while waiting for a connection
        while True:
            blink_idle_red()
            server_socket.settimeout(0.1)  # Allow blinking during idle
            try:
                conn, addr = server_socket.accept()
                break
            except socket.timeout:
                continue

        print(f"Connected by {addr}")

        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    print("Connection closed by client.")
                    break
                
                # Parse received data
                try:
                    parts = data.split(",")
                    if parts[0] == "BEEP":  # Long beep command
                        cam_id = int(parts[1])
                        duration = float(parts[2])
                        print(f"Camera {cam_id}: Non-Blocking Beep for {duration} seconds")
                        non_blocking_beep(cam_id, duration)
                    else:  # Servo control
                        cam_id, horizontal_angle, vertical_angle = map(int, parts)
                        print(f"Camera {cam_id}: Horizontal Angle={horizontal_angle}, Vertical Angle={vertical_angle}")
                        
                        # Set servo angles for the specified camera
                        if cam_id in servo_pins:
                            set_angle(servo_pins[cam_id]["horizontal"], horizontal_angle)
                            set_angle(servo_pins[cam_id]["vertical"], vertical_angle)
                            indicate_action(cam_id)  # Change LED and beep
                        else:
                            print(f"Invalid camera ID: {cam_id}")
                except ValueError:
                    print(f"Invalid data format: {data}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
            print("Client disconnected.")
finally:
    # Cleanup and stop servos
    for cam_id, pins in servo_pins.items():
        for pin in pins.values():
            pi.set_servo_pulsewidth(pin, 0)  # Stop the servo
    for cam_id, leds in led_pins.items():
        for pin in leds.values():
            pi.write(pin, 0)  # Turn off LEDs
        pi.write(buzzer_pins[cam_id], 0)  # Turn off buzzers
    pi.stop()
    server_socket.close()
