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
#WIFI_SSID = "BELL470"
#WIFI_PASSWORD = "911A9DEC7146"
WIFI_SSID = "THIRDEARTH"
WIFI_PASSWORD = "Mr.LamYo"
HTTP_PORT = 80

# Hardware pins
BUTTON_PIN = 16
LED_PIN = 17
I2C1_SDA = 0
I2C1_SCL = 1

# IMU threshold for direction detection
GYRO_THRESHOLD = 150

# ============ GLOBAL STATE ============
system_on = False
imu1 = None
devices_connected = False
web_socket = None
connected_clients = {}
current_car_command = {'direction': 'stop', 'speed': 0}
last_finger1_direction = 'center'

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
    global imu1, devices_connected
    
    button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
    led = Pin(LED_PIN, Pin.OUT)
    led.value(0)
    
    # Initialize IMU sensors
    if IMU_AVAILABLE and MPU6050:
        try:
            i2c1 = I2C(0, sda=Pin(I2C1_SDA), scl=Pin(I2C1_SCL))
            imu1 = MPU6050(i2c1)
            
            # Test sensors
            _ = imu1.gyro
            devices_connected = True
            print('[HARDWARE] IMU sensor connected')
        except Exception as e:
            print('[HARDWARE] IMU sensor failed:', e)
            imu1 = None
            devices_connected = False
    
    return button, led

# ============ CAR COMMAND CONTROL ============
def set_car_command(direction, speed=70):
    """Update current car command"""
    global current_car_command
    current_car_command = {'direction': direction, 'speed': speed}
    print(f'[CAR] Command: {direction.upper()} @ {speed}%')

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
                set_car_command('forward', 70)
            elif finger1_direction == 'down':
                set_car_command('backward', 70)
            elif finger1_direction == 'left':
                set_car_command('left', 60)
            elif finger1_direction == 'right':
                set_car_command('right', 60)
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
        s.listen(1)
        s.setblocking(False)
        web_socket = s
        print(f'[HTTP] Server started on port {HTTP_PORT}')
    except Exception as e:
        print('[HTTP] Server failed:', e)
        web_socket = None

def send_response(conn, status, content_type, body):
    """Send HTTP response"""
    try:
        response = f'HTTP/1.0 {status}\r\nContent-Type: {content_type}\r\n\r\n'
        conn.send(response.encode())
        if body:
            conn.send(body if isinstance(body, bytes) else body.encode())
    except:
        pass

def handle_request(conn, addr):
    """Handle incoming HTTP request"""
    global connected_clients, system_on
    
    try:
        conn.settimeout(0.5)
        request = conn.recv(2048)
        if not request:
            conn.close()
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
                    send_response(conn, '200 OK', 'text/html', b'')
                    while True:
                        chunk = f.read(512)
                        if not chunk:
                            break
                        conn.send(chunk)
            except:
                send_response(conn, '404 Not Found', 'text/html', '<h1>File not found</h1>')
        
        elif method == 'GET' and path == '/sensors':
            # Return sensor data
            finger1_state = 'center'
            
            if devices_connected and imu1:
                try:
                    finger1_state = get_finger_direction(imu1.gyro)
                except:
                    pass
            
            data = {
                'client_count': len(connected_clients),
                'finger1': finger1_state,
                'car_command': current_car_command
            }
            send_response(conn, '200 OK', 'application/json', json.dumps(data))
        
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
        
        elif method == 'POST' and path == '/press':
            # Handle button press from web app
            body_start = request_text.find('\r\n\r\n')
            if body_start != -1:
                body = request_text[body_start + 4:]
                try:
                    data = json.loads(body)
                    button_label = data.get('button', '').lower()
                    
                    print(f'[WEB] Button pressed: {button_label.upper()}')
                    
                    # Map button to car command
                    if button_label == 'forward':
                        set_car_command('forward', 70)
                    elif button_label == 'backward':
                        set_car_command('backward', 70)
                    elif button_label == 'left':
                        set_car_command('left', 60)
                    elif button_label == 'right':
                        set_car_command('right', 60)
                    elif button_label == 'brake':
                        set_car_command('stop', 0)
                    elif button_label == 'attack1':
                        set_car_command('spin_left', 50)
                    elif button_label == 'attack2':
                        set_car_command('spin_right', 50)
                    
                    response_data = {'status': 'ok', 'pressed': button_label}
                    send_response(conn, '200 OK', 'application/json', json.dumps(response_data))
                except:
                    send_response(conn, '400 Bad Request', 'application/json', '{"error":"invalid json"}')
        
        else:
            # 404 for unknown routes
            send_response(conn, '404 Not Found', 'text/html', '<h1>Not Found</h1>')
        
        conn.close()
    except Exception as e:
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
    print('🎮 WEARABLE CONTROLLER - CLEAN VERSION')
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
    
    # Main loop
    while True:
        # Handle button press (toggle system on/off)
        if button.value() == 1:
            system_on = not system_on
            led.value(1 if system_on else 0)
            print(f'[SYSTEM] {"ON" if system_on else "OFF"}')
            sleep(0.5)
        
        # Process IMU input when system is on
        if system_on:
            process_imu_input()
        
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
        
        sleep(0.1)

# Start the program
if __name__ == '__main__':
    main()


