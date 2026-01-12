"""
NAVIGATION MODE
Handles car control via gyroscope for wireless robot car
"""

try:
    import ujson as json
except:
    import json
import socket

# Module-level state variables
car_enabled = False
car_ip = None
car_port = 8080
last_car_command = 'stop'
last_car_send_time = 0


def test_ghost_connection(ip, port):
    """Test connection to Ghost Pico"""
    if ip is None:
        print('[GHOST] No IP configured')
        return False
    
    try:
        print(f'[GHOST] Testing connection to {ip}:{port}...')
        addr = socket.getaddrinfo(ip, port)[0][-1]
        s = socket.socket()
        s.settimeout(2.0)
        s.connect(addr)
        
        # Send test ping
        cmd = json.dumps({'direction': 'stop', 'speed': 0})
        s.send(cmd.encode('utf-8'))
        response = s.recv(256)
        s.close()
        
        print('[GHOST] Connection successful!')
        return True
        
    except Exception as e:
        print(f'[GHOST] Connection failed: {e}')
        return False


def send_car_command(ip, port, direction, speed, ticks_ms):
    """Send command to car via WiFi"""
    global last_car_command, last_car_send_time
    
    if not car_enabled or ip is None:
        return False
    
    # Throttle commands - only send if changed or 300ms elapsed
    now = ticks_ms()
    if direction == last_car_command and (now - last_car_send_time) < 300:
        return True
    
    try:
        addr = socket.getaddrinfo(ip, port)[0][-1]
        s = socket.socket()
        s.settimeout(0.5)
        s.connect(addr)
        
        cmd = json.dumps({'direction': direction, 'speed': speed})
        s.send(cmd.encode('utf-8'))
        s.recv(256)  # Get ACK
        s.close()
        
        last_car_command = direction
        last_car_send_time = now
        return True
        
    except Exception as e:
        print(f'[CAR] Send error: {e}')
        return False


def handle_navigation_mode(gyroscope1, ticks_ms):
    """
    Navigation mode handler - controls robot car via gyroscope
    Returns: (car_enabled, car_ip)
    """
    global car_enabled, car_ip, car_port
    
    # Enable car control and connect to Ghost when entering Navigation Mode
    if not car_enabled:
        print('\n' + '='*50)
        print('[NAV] Navigation Mode Activated')
        print('='*50)
        
        # Set Ghost Pico IP address
        car_ip = '192.168.2.100'  # CHANGE THIS to match your Ghost Pico's IP!
        
        # Test connection to Ghost
        print(f'[NAV] Connecting to Ghost Pico at {car_ip}:{car_port}...')
        if test_ghost_connection(car_ip, car_port):
            car_enabled = True
            print('[NAV] Ghost connected - Car control ready!')
            print('='*50 + '\n')
        else:
            car_enabled = False
            car_ip = None
            print('[NAV] Failed to connect to Ghost - Check:')
            print('  1. Ghost.py is running on car Pico')
            print('  2. Car Pico IP matches car_ip setting')
            print('  3. Both Picos on same WiFi network')
            print('='*50 + '\n')
            return car_enabled, car_ip
    
    # Only control car if successfully connected
    if car_enabled:
        # Use gyroscope1 Z-axis (left/right rotation) for steering
        z_rotation = gyroscope1.z
        
        # Determine direction based on Z-axis rotation (left/right tilt)
        if z_rotation < -100:
            send_car_command(car_ip, car_port, 'spin_left', 60, ticks_ms)
        elif z_rotation < -50:
            send_car_command(car_ip, car_port, 'left', 70, ticks_ms)
        elif z_rotation > 100:
            send_car_command(car_ip, car_port, 'spin_right', 60, ticks_ms)
        elif z_rotation > 50:
            send_car_command(car_ip, car_port, 'right', 70, ticks_ms)
        else:
            # Use Y-axis for forward/backward when not turning
            y_rotation = gyroscope1.y
            if y_rotation < -60:
                send_car_command(car_ip, car_port, 'forward', 75, ticks_ms)
            elif y_rotation > 60:
                send_car_command(car_ip, car_port, 'backward', 65, ticks_ms)
            else:
                send_car_command(car_ip, car_port, 'stop', 0, ticks_ms)
    
    return car_enabled, car_ip


def exit_navigation_mode():
    """Clean exit from navigation mode - stop car and disconnect"""
    global car_enabled, car_ip, car_port
    
    if car_enabled:
        print('\n[NAV] Exiting Navigation Mode...')
        # Send stop command
        try:
            addr = socket.getaddrinfo(car_ip, car_port)[0][-1]
            s = socket.socket()
            s.settimeout(0.5)
            s.connect(addr)
            cmd = json.dumps({'direction': 'stop', 'speed': 0})
            s.send(cmd.encode('utf-8'))
            s.recv(256)
            s.close()
        except:
            pass
        
        car_enabled = False
        car_ip = None
        print('[NAV] Car stopped - Ghost disconnected\n')
    
    return car_enabled, car_ip
