"""
Wearable Controller - Clean Version
Controls robot car via IMU gestures and web interface
"""

from utime import sleep, ticks_ms
from machine import Pin, I2C, PWM
import network
import socket

try:
    import ujson as json
except:
    import json

try:
    from imu import MPU6050
    IMU_AVAILABLE = True
except:
    IMU_AVAILABLE = False
    MPU6050 = None

# ============ CONFIGURATION ============
WIFI_SSID = "BELL470"
WIFI_PASSWORD = "911A9DEC7146"
#WIFI_SSID = "THIRDEARTH"
#WIFI_PASSWORD = "Mr.LamYo"
HTTP_PORT = 80

# Hardware pins
BUTTON_PIN = 16
LED_PIN = 17
SERVO_PIN = 15  # Servo control pin
BUZZER_PIN = 22  # Buzzer for sound effects
I2C1_SDA = 4
I2C1_SCL = 5

# IMU threshold for direction detection
GYRO_THRESHOLD = 50

# ============ GLOBAL STATE ============
system_on = False
dancing = False
dance_step = 0
dance_step_start_time = 0
song_note_index = 0
imu1 = None
imu2 = None
servo = None
buzzer = None
devices_connected = False
web_socket = None
connected_clients = {}
current_car_command = {
    'direction': 'stop', 
    'speed': 0,
    'servo_angle': 180,
    'status_text': 'Ready',
    'status_emoji': '🚗',
    'status_color': '52,152,219'
}
# Separate tracking for movement vs attack status
movement_status = {
    'text': 'Ready',
    'emoji': '🚗',
    'color': '52,152,219'
}
attack_status = {
    'text': 'Return',
    'emoji': '⚡',
    'color': '155,89,182'
}
last_finger1_direction = 'center'
last_finger2_direction = 'center'

# ============ WIFI SETUP ============
def setup_wifi():
    """Connect to WiFi network"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('[WIFI] Connecting to:', WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        timeout = 60
        start = ticks_ms()
        while not wlan.isconnected() and (ticks_ms() - start) < (timeout * 1000):
            sleep(1)
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print('\n' + '='*50)
        print('[WIFI] Connected!')
        print('[WIFI] IP Address:', ip)
        print('='*50 + '\n')
        return ip
    else:
        print('[WIFI] Connection failed!')
        return None

# ============ HARDWARE SETUP ============
def setup_hardware():
    """Initialize hardware components"""
    global imu1, imu2, devices_connected, servo, buzzer
    
    button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
    led = Pin(LED_PIN, Pin.OUT)
    led.value(0)
    
    # Initialize buzzer
    try:
        buzzer = PWM(Pin(BUZZER_PIN))
        buzzer.duty_u16(0)  # Start silent
        print('[HARDWARE] Buzzer initialized')
    except Exception as e:
        print(f'[HARDWARE] Buzzer failed: {e}')
        buzzer = None
    
    # Servo is only on the robot (ghost.py), not on controller
    servo = None
    
    # Initialize IMU sensors
    if IMU_AVAILABLE and MPU6050:
        try:
            i2c1 = I2C(0, sda=Pin(I2C1_SDA), scl=Pin(I2C1_SCL))
            imu1 = MPU6050(i2c1)
            
            # Test sensor
            _ = imu1.gyro
            devices_connected = True
            print('[HARDWARE] IMU sensor connected')
        except Exception as e:
            print('[HARDWARE] IMU sensor failed:', e)
            imu1 = None
            devices_connected = False
    
    return button, led

# ============ BUZZER CONTROL ============
def play_pacman_ghost():
    """Play Pac-Man ghost sound (oscillating tone)"""
    global buzzer
    if buzzer is None:
        return
    
    try:
        # Pac-Man ghost sound: oscillating between two notes
        notes = [330, 262]  # E4 and C4
        for freq in notes:
            buzzer.freq(freq)
            buzzer.duty_u16(500)  # Half volume (reduced from 1000)
            sleep(0.2)
        buzzer.duty_u16(0)  # Brief silence
        sleep(0.05)
    except:
        pass

def stop_buzzer():
    """Stop buzzer sound"""
    global buzzer
    if buzzer:
        buzzer.duty_u16(0)

def play_victory_song():
    """Play victory/celebration song (continuous melody loop)"""
    global buzzer, song_note_index
    if buzzer is None:
        return
    
    try:
        # Victory melody that loops continuously
        melody = [
            523,   # C5
            659,   # E5
            784,   # G5
            1047,  # C6
            784,   # G5
            659,   # E5
            523,   # C5
            784,   # G5
        ]
        
        # Play current note
        buzzer.freq(melody[song_note_index])
        buzzer.duty_u16(500)
        
        # Move to next note (loop back to start)
        song_note_index = (song_note_index + 1) % len(melody)
    except:
        pass

def dance_move():
    """Execute one dance step (non-blocking state machine)"""
    global current_car_command, dancing, dance_step, dance_step_start_time
    if not dancing:
        return
    
    # Simplified smooth dance sequence
    # Each move: (servo_angle, direction, speed, duration_ms)
    dance_sequence = [
        (45, 'spin_left', 60, 400),       # Step 0: Swing left with servo
        (90, 'stop', 0, 150),              # Step 1: Center, brief pause
        (135, 'spin_right', 60, 400),      # Step 2: Swing right with servo
        (90, 'stop', 0, 150),              # Step 3: Center, brief pause
        (45, 'spin_left', 60, 400),        # Step 4: Swing left again
        (90, 'stop', 0, 150),              # Step 5: Center, brief pause
        (135, 'spin_right', 60, 400),      # Step 6: Swing right again
        (90, 'stop', 0, 150),              # Step 7: Center, brief pause
    ]
    
    now = ticks_ms()
    
    # Initialize step timing
    if dance_step_start_time == 0:
        dance_step_start_time = now
    
    # Check if current step duration has elapsed
    if dance_step < len(dance_sequence):
        servo_pos, direction, speed, duration = dance_sequence[dance_step]
        
        # Update command for current step
        set_car_command(direction, speed, 'Dancing', '🕺', '255,215,0', servo_angle=servo_pos)
        
        # Check if it's time to move to next step
        if now - dance_step_start_time >= duration:
            dance_step += 1
            dance_step_start_time = now
    else:
        # Restart dance sequence
        dance_step = 0
        dance_step_start_time = now

# ============ SERVO CONTROL ============
def set_servo_angle(angle):
    """Set servo to specific angle (0-180 degrees)"""
    global servo
    
    if servo is None:
        print('[SERVO] Not initialized')
        return False
    
    try:
        # Convert angle to duty cycle
        # Servo pulse width: 1ms (0°) to 2ms (180°) at 50Hz
        # Duty cycle range: ~1600 to ~8000 for 16-bit PWM
        min_duty = 1600   # 0 degrees
        max_duty = 8000   # 180 degrees
        
        # Clamp angle between 0 and 180
        angle = max(0, min(180, angle))
        
        # Calculate duty cycle
        duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
        servo.duty_u16(duty)
        
        print(f'[SERVO] Angle set to: {angle}°')
        return True
    except Exception as e:
        print(f'[SERVO] Failed to set angle: {e}')
        return False

# ============ CAR COMMAND CONTROL ============
def set_car_command(direction, speed=70, status_text=None, status_emoji='🚗', status_color='52,152,219', servo_angle=None, is_attack=False):
    """Update current car command with display information"""
    global current_car_command, movement_status, attack_status
    
    if status_text is None:
        status_text = direction.capitalize()
    
    # Preserve current servo angle if not specified
    if servo_angle is None:
        servo_angle = current_car_command.get('servo_angle', 0)
    
    current_car_command = {
        'direction': direction, 
        'speed': speed,
        'servo_angle': servo_angle,
        'status_text': status_text,
        'status_emoji': status_emoji,
        'status_color': status_color
    }
    
    # Update appropriate status tracker
    if is_attack:
        attack_status = {
            'text': status_text,
            'emoji': status_emoji,
            'color': status_color
        }
    else:
        movement_status = {
            'text': status_text,
            'emoji': status_emoji,
            'color': status_color
        }
    
    print(f'[CAR] Command: {direction.upper()} @ {speed}% - {status_emoji} {status_text}')

def get_finger_direction(gyro):
    """Get direction from gyroscope reading"""
    if gyro.x < -GYRO_THRESHOLD:
        return 'down'
    elif gyro.x > GYRO_THRESHOLD:
        return 'up'
    elif gyro.y < -GYRO_THRESHOLD:
        return 'left'
    elif gyro.y > GYRO_THRESHOLD:
        return 'right'
    return 'center'

def process_imu_input():
    """Process IMU sensor input and update car command"""
    global last_finger1_direction
    
    if not devices_connected or not imu1:
        return
    
    try:
        gyro1 = imu1.gyro
        finger1_direction = get_finger_direction(gyro1)
        
        # Only update if direction changed and not center
        if finger1_direction != last_finger1_direction:
            last_finger1_direction = finger1_direction
            print(f'[IMU] Finger 1: {finger1_direction.upper()}')
            
            # Map direction to car command (center does nothing - maintains last command)
            if finger1_direction == 'up':
                set_car_command('forward', 100, 'Forward', '⬆️', '52,152,219')
            elif finger1_direction == 'down':
                set_car_command('backward', 100, 'Backward', '⬇️', '230,126,34')
            elif finger1_direction == 'left':
                set_car_command('left', 50, 'Left', '⬅️', '155,89,182')
            elif finger1_direction == 'right':
                set_car_command('right', 50, 'Right', '➡️', '26,188,156')
            # Center position: do nothing, keep last command active
    except Exception as e:
        pass

# ============ HTTP SERVER ============
def start_http_server():
    """Start HTTP server on port 80"""
    global web_socket
    
    try:
        addr = socket.getaddrinfo('0.0.0.0', HTTP_PORT)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(5)  # Increased backlog for concurrent connections
        s.setblocking(False)
        web_socket = s
        print(f'[HTTP] Server started on port {HTTP_PORT}')
    except Exception as e:
        print('[HTTP] Server failed:', e)
        web_socket = None

def send_response(conn, status, content_type, body):
    """Send HTTP response with CORS headers"""
    try:
        # Convert body to bytes if needed
        if body is None:
            body_bytes = b''
        elif isinstance(body, bytes):
            body_bytes = body
        else:
            body_bytes = str(body).encode('utf-8')
        
        # Build complete response with headers
        response_header = f'HTTP/1.1 {status}\r\n'
        response_header += f'Content-Type: {content_type}\r\n'
        response_header += f'Content-Length: {len(body_bytes)}\r\n'
        response_header += 'Access-Control-Allow-Origin: *\r\n'
        response_header += 'Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n'
        response_header += 'Access-Control-Allow-Headers: Content-Type\r\n'
        response_header += 'Connection: close\r\n'
        response_header += '\r\n'
        
        # Send header and body together
        conn.sendall(response_header.encode('utf-8') + body_bytes)
    except Exception as e:
        print(f'[RESPONSE] Error sending: {e}')
        pass

def handle_request(conn, addr):
    """Handle incoming HTTP request"""
    global connected_clients, system_on
    
    try:
        conn.settimeout(0.5)  # 500ms for instant response
        request = conn.recv(2048)  # Optimized buffer size
        if not request:
            try:
                conn.close()
            except:
                pass
            return
        
        # Parse request
        request_text = request.decode('utf-8')
        lines = request_text.split('\r\n')
        method, path, _ = lines[0].split(' ')
        
        # Track client
        client_ip = addr[0]
        connected_clients[client_ip] = ticks_ms()
        
        # Route requests
        if method == 'GET' and path == '/':
            # Serve web interface
            try:
                with open('Controller.html', 'rb') as f:
                    content = f.read()
                send_response(conn, '200 OK', 'text/html', content)
            except Exception as e:
                print(f'[HTML] Error loading file: {e}')
                send_response(conn, '404 Not Found', 'text/html', '<h1>File not found</h1>')
        
        elif method == 'GET' and path == '/sensors':
            # Return sensor data with robust error handling
            try:
                finger1_state = 'center'
                
                if devices_connected and imu1:
                    try:
                        gyro_data = imu1.gyro
                        if gyro_data:
                            finger1_state = get_finger_direction(gyro_data)
                    except Exception as e:
                        print(f'[SENSORS] IMU read error: {e}')
                        finger1_state = 'center'
                
                # Safely get current car command fields with defaults
                data = {
                    'client_count': max(0, len(connected_clients)),
                    'finger1': str(finger1_state),
                    'status_text': str(movement_status.get('text', 'Ready')),
                    'status_emoji': str(movement_status.get('emoji', '🚗')),
                    'status_color': str(movement_status.get('color', '52,152,219')),
                    'attack_text': str(attack_status.get('text', 'Return')),
                    'attack_emoji': str(attack_status.get('emoji', '⚡')),
                    'attack_color': str(attack_status.get('color', '155,89,182'))
                }
                
                response_json = json.dumps(data)
                send_response(conn, '200 OK', 'application/json', response_json)
            except Exception as e:
                print(f'[SENSORS] Endpoint error: {e}')
                error_data = {'error': 'sensor_read_failed', 'client_count': 0, 'finger1': 'center', 'status_text': 'Error', 'status_emoji': '⚠️', 'status_color': '231,76,60'}
                send_response(conn, '500 Internal Server Error', 'application/json', json.dumps(error_data))
        
        elif method == 'GET' and path == '/state':
            # Return system state
            data = {
                'power': 'ON' if system_on else 'OFF',
                'devices_connected': devices_connected,
                'network': 'Connected (STA)',
                'clients': len(connected_clients),
                'song': 'None'
            }
            send_response(conn, '200 OK', 'application/json', json.dumps(data))
        
        elif method == 'GET' and path == '/car_command':
            # Return current car command (for ghost car to poll)
            send_response(conn, '200 OK', 'application/json', json.dumps(current_car_command))
        
        elif method == 'OPTIONS':
            # Handle CORS preflight
            send_response(conn, '204 No Content', 'text/plain', '')
        
        elif method == 'POST' and path == '/press':
            # Handle button press from web app with validation
            try:
                # Find body start
                body_start = request_text.find('\r\n\r\n')
                if body_start == -1:
                    print('[PRESS] No body separator found')
                    send_response(conn, '400 Bad Request', 'application/json', '{"error":"no_body"}')
                    conn.close()
                    return
                
                # Extract and clean body
                body = request_text[body_start + 4:]
                
                # Remove any trailing nulls or whitespace
                body = body.rstrip('\x00').strip()
                
                if not body:
                    print('[PRESS] Empty body after extraction')
                    send_response(conn, '400 Bad Request', 'application/json', '{"error":"empty_body"}')
                    conn.close()
                    return
                
                try:
                    # Parse JSON
                    data = json.loads(body)
                    
                    # Validate button field exists
                    if 'button' not in data:
                        print('[PRESS] Missing button field in JSON')
                        send_response(conn, '400 Bad Request', 'application/json', '{"error":"missing_button"}')
                        conn.close()
                        return
                    
                    button_label = str(data['button']).lower().strip()
                    
                    if not button_label:
                        print('[PRESS] Empty button value')
                        send_response(conn, '400 Bad Request', 'application/json', '{"error":"empty_button"}')
                        conn.close()
                        return
                    
                    print(f'[WEB] Button: {button_label.upper()}')
                    
                    # Map button to car command
                    if button_label == 'forward':
                        set_car_command('forward', 100, 'Forward', '⬆️', '52,152,219')
                    elif button_label == 'backward':
                        set_car_command('backward', 100, 'Backward', '⬇️', '230,126,34')
                    elif button_label == 'left':
                        set_car_command('left', 50, 'Left', '⬅️', '155,89,182')
                    elif button_label == 'right':
                        set_car_command('right', 50, 'Right', '➡️', '26,188,156')
                    elif button_label == 'brake':
                        set_car_command('stop', 0, 'BRAKE', '🛑', '231,76,60')
                    elif button_label == 'attack1':
                        # Control robot servo (90 degrees) - keep current direction
                        current_dir = current_car_command.get('direction', 'stop')
                        current_spd = current_car_command.get('speed', 0)
                        set_car_command(current_dir, current_spd, 'Extendo', '⚔️', '243,156,18', servo_angle=90, is_attack=True)
                    elif button_label == 'attack2':
                        # Control robot servo (0 degrees) - keep current direction
                        current_dir = current_car_command.get('direction', 'stop')
                        current_spd = current_car_command.get('speed', 0)
                        set_car_command(current_dir, current_spd, 'Pinch', '💥', '231,76,60', servo_angle=0, is_attack=True)
                    elif button_label == 'attack3':
                        # Control robot servo (180 degrees) - keep current direction
                        current_dir = current_car_command.get('direction', 'stop')
                        current_spd = current_car_command.get('speed', 0)
                        set_car_command(current_dir, current_spd, 'Return', '⚡', '155,89,182', servo_angle=180, is_attack=True)
                    elif button_label == 'dance_start':
                        # Start dancing mode
                        global dancing
                        dancing = True
                        set_car_command('spin_left', 60, 'Dancing', '🕺', '255,215,0', servo_angle=90)
                        print('[DANCE] Started')
                    elif button_label == 'dance_stop':
                        # Stop dancing mode
                        global dancing
                        dancing = False
                        set_car_command('stop', 0, 'Dance Stopped', '🛑', '231,76,60', servo_angle=180)
                        stop_buzzer()
                        print('[DANCE] Stopped')
                    else:
                        print(f'[PRESS] Unknown button: {button_label}')
                        send_response(conn, '400 Bad Request', 'application/json', '{"error":"unknown_button"}')
                        conn.close()
                        return
                    
                    response_data = {'status': 'ok', 'pressed': button_label}
                    send_response(conn, '200 OK', 'application/json', json.dumps(response_data))
                    
                except ValueError as e:
                    print(f'[PRESS] JSON parse error: {e} | Body: {repr(body[:100])}')
                    send_response(conn, '400 Bad Request', 'application/json', '{"error":"invalid_json"}')
                except KeyError as e:
                    print(f'[PRESS] Missing key: {e}')
                    send_response(conn, '400 Bad Request', 'application/json', '{"error":"missing_field"}')
                except Exception as e:
                    print(f'[PRESS] Processing error: {e}')
                    send_response(conn, '500 Internal Server Error', 'application/json', '{"error":"processing_failed"}')
            except Exception as e:
                print(f'[PRESS] Endpoint error: {e}')
                send_response(conn, '500 Internal Server Error', 'application/json', '{"error":"request_failed"}')
        
        else:
            # 404 for unknown routes
            send_response(conn, '404 Not Found', 'text/html', '<h1>Not Found</h1>')
        
        try:
            conn.close()
        except:
            pass
    except OSError as e:
        # Handle socket errors gracefully
        print(f'[REQUEST] Socket error: {e}')
        try:
            conn.close()
        except:
            pass
    except Exception as e:
        print(f'[REQUEST] Error: {e}')
        try:
            conn.close()
        except:
            pass

def cleanup_old_clients():
    """Remove stale client connections"""
    global connected_clients
    now = ticks_ms()
    to_remove = [ip for ip, timestamp in connected_clients.items() if now - timestamp > 60000]
    for ip in to_remove:
        del connected_clients[ip]

# ============ MAIN LOOP ============
def main():
    """Main program loop"""
    global system_on
    
    print('\n' + '='*50)
    print('🎮 WEARABLE CONTROLLER')
    print('='*50 + '\n')
    
    # Setup
    my_ip = setup_wifi()
    if not my_ip:
        print('[ERROR] Cannot start without WiFi')
        return
    
    button, led = setup_hardware()
    start_http_server()
    
    if not web_socket:
        print('[ERROR] Cannot start without HTTP server')
        return
    
    print('[READY] Controller initialized')
    print(f'[READY] Web app: http://{my_ip}')
    print(f'[READY] Ghost car endpoint: http://{my_ip}/car_command\n')
    
    last_cleanup = ticks_ms()
    last_sound = ticks_ms()
    last_dance = ticks_ms()
    last_victory = ticks_ms()
    
    # Main loop
    while True:
        # Handle button press (toggle system on/off)
        if button.value() == 1:
            system_on = not system_on
            led.value(1 if system_on else 0)
            print(f'[SYSTEM] {"ON" if system_on else "OFF"}')
            
            # When turning off, set to brake and return position
            if not system_on:
                set_car_command('stop', 0, 'BRAKE', '🛑', '231,76,60', servo_angle=180)
                print('[SYSTEM] Reset to BRAKE and RETURN position')
                stop_buzzer()  # Stop sound when system turns off
                global dancing, dance_step, dance_step_start_time, song_note_index
                dancing = False  # Stop dancing when system turns off
                dance_step = 0
                dance_step_start_time = 0
                song_note_index = 0
            
            sleep(0.5)
        
        # Handle dancing mode
        if system_on and dancing:
            # Execute dance move state machine (non-blocking)
            dance_move()
            
            # Play continuous melody during dance
            now = ticks_ms()
            if now - last_victory > 250:  # Change note every 250ms for melody
                play_victory_song()
                last_victory = now
        
        # Process IMU input when system is on and NOT dancing
        elif system_on:
            process_imu_input()
            # Ensure buzzer is off when not dancing
            if buzzer:
                buzzer.duty_u16(0)
        else:
            # System off - ensure buzzer is off
            if buzzer:
                buzzer.duty_u16(0)
        
        # Handle HTTP requests
        if web_socket:
            try:
                conn, addr = web_socket.accept()
                handle_request(conn, addr)
            except:
                pass
        
        # Cleanup old clients every 5 seconds
        now = ticks_ms()
        if now - last_cleanup > 5000:
            cleanup_old_clients()
            last_cleanup = now
        
        sleep(0.001)  # 1ms for near-instant response

# Start the program
if __name__ == '__main__':
    main()

