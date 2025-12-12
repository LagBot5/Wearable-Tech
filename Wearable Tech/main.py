from imu import MPU6050
from utime import sleep, ticks_ms
from machine import Pin, I2C, PWM

import network
import socket
import urequests as requests

try:
    import ujson as json
except Exception:
    import json

ssid = "THIRDEARTH"
pw = "Mr.LamYo"

# Prefer STA-only operation: attempt to join the router network and
# allow other devices on the same router to connect to the Pico.
network_mode = 'unknown'
try:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if ssid:
        wlan.connect(ssid, pw)
    # wait up to 60 seconds for connection
    wait_seconds = 60
    start = ticks_ms()
    while not wlan.isconnected() and (ticks_ms() - start) < (wait_seconds * 1000):
        print('Connecting to WiFi...')
        sleep(1)

    if wlan.isconnected():
        print('Connected to WiFi')
        wlanInfo = wlan.ifconfig()
        print("My Pico's IP address is:", wlanInfo[0])
        network_mode = 'sta'
    else:
        # Do not start an Access Point — the user requested STA be used for other devices.
        print(f"Warning: STA connection failed after {wait_seconds}s; AP fallback disabled.")
        network_mode = 'none'
except Exception as e:
    print('Network setup error:', e)
    network_mode = 'error'

# HTTP server for web UI
web_sock = None
current_mode = 'idle'  # track current mode from web button presses
# track connected HTTP client IPs -> timestamp (ms)
connected_clients = {}

button = Pin(16, Pin.IN, Pin.PULL_DOWN)
StateLed = Pin(17, Pin.OUT)
state = 0

speaker = PWM(Pin(22))

tones = {
    'C0': 16, 'C#0': 17, 'D0': 18, 'D#0': 19, 'E0': 21, 'F0': 22,
    'F#0': 23, 'G0': 24, 'G#0': 26, 'A0': 28, 'A#0': 29, 'B0': 31,
    'C1': 33, 'C#1': 35, 'D1': 37, 'D#1': 39, 'E1': 41, 'F1': 44,
    'F#1': 46, 'G1': 49, 'G#1': 52, 'A1': 55, 'A#1': 58, 'B1': 62,
    'C2': 65, 'C#2': 69, 'D2': 73, 'D#2': 78, 'E2': 82, 'F2': 87,
    'F#2': 92, 'G2': 98, 'G#2': 104, 'A2': 110, 'A#2': 117, 'B2': 123,
    'C3': 131, 'C#3': 139, 'D3': 147, 'D#3': 156, 'E3': 165, 'F3': 175,
    'F#3': 185, 'G3': 196, 'G#3': 208, 'A3': 220, 'A#3': 233, 'B3': 247,
    'C4': 262, 'C#4': 277, 'D4': 294, 'D#4': 311, 'E4': 330, 'F4': 349,
    'F#4': 370, 'G4': 392, 'G#4': 415, 'A4': 440, 'A#4': 466, 'B4': 494,
    'C5': 523, 'C#5': 554, 'D5': 587, 'D#5': 622, 'E5': 659, 'F5': 698,
    'F#5': 740, 'G5': 784, 'G#5': 831, 'A5': 880, 'A#5': 932, 'B5': 988,
    'C6': 1047, 'C#6': 1109, 'D6': 1175, 'D#6': 1245, 'E6': 1319, 'F6': 1397,
    'F#6': 1480, 'G6': 1568, 'G#6': 1661, 'A6': 1760, 'A#6': 1865, 'B6': 1976,
    'C7': 2093, 'C#7': 2217, 'D7': 2349, 'D#7': 2489, 'E7': 2637, 'F7': 2794,
    'F#7': 2960, 'G7': 3136, 'G#7': 3322, 'A7': 3520, 'A#7': 3729, 'B7': 3951,
    'C8': 4186, 'C#8': 4435, 'D8': 4699, 'D#8': 4978, 'E8': 5274, 'F8': 5588,
    'F#8': 5920, 'G8': 6272, 'G#8': 6645, 'A8': 7040, 'A#8': 7459, 'B8': 7902,
    'C9': 8372, 'C#9': 8870, 'D9': 9397, 'D#9': 9956, 'E9': 10548, 'F9': 11175,
    'F#9': 11840, 'G9': 12544, 'G#9': 13290, 'A9': 14080, 'A#9': 14917, 'B9': 15804
}

def playtone(frequency):
    speaker.duty_u16(5000) # turn the PWM duty to 50%
    speaker.freq(frequency)

def bequiet():
    speaker.duty_u16(0) # turn off the speaker PWM

def start_http_server():
    """Start a non-blocking HTTP server on port 80."""
    global web_sock
    try:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass
        s.bind(addr)
        s.listen(1)
        s.setblocking(False)
        web_sock = s
        print('[HTTP] Server listening on', addr)
    except Exception as e:
        print('[HTTP] Failed to start:', e)
        web_sock = None

def handle_http_request(conn, addr):
    """Handle a simple HTTP request: GET / or POST /press."""
    global current_mode
    global connected_clients
    try:
        conn.settimeout(0.5)
        req = b''
        try:
            req = conn.recv(2048)
        except Exception:
            pass
        if not req:
            conn.close()
            return
        try:
            text = req.decode('utf-8')
        except Exception:
            text = str(req)

        # record client IP activity
        try:
            client_ip = addr[0]
            connected_clients[client_ip] = ticks_ms()
        except Exception:
            pass
        
        first_line = text.split('\r\n', 1)[0]
        parts = first_line.split(' ')
        if len(parts) < 2:
            conn.close()
            return
        method, path = parts[0], parts[1]
        
        # GET / returns the web UI (Controller.html)
        if method == 'GET' and path == '/':
            try:
                with open('Controller.html', 'r') as f:
                    body = f.read()
            except Exception:
                body = f'<h1>Pico Wearable Server</h1><p>Mode: {current_mode}</p>'
            resp = 'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: {length}\r\n\r\n{body}'.format(length=len(body), body=body)
            try:
                conn.send(resp.encode('utf-8'))
            except Exception:
                pass
            conn.close()
            return

        # GET /sensors - return current IMU sensor readings as JSON
        if method == 'GET' and path == '/sensors':
            try:
                g1 = imu1.gyro
                a1 = imu1.accel
                g2 = imu2.gyro
                a2 = imu2.accel
                # prune clients older than 60s and collect recent list
                now = ticks_ms()
                recent = []
                to_remove = []
                for ip, t in connected_clients.items():
                    if now - t <= 60000:
                        recent.append(ip)
                    else:
                        to_remove.append(ip)
                for ip in to_remove:
                    try:
                        del connected_clients[ip]
                    except Exception:
                        pass

                payload = {
                    'mode': current_mode,
                    'clients': recent,
                    'client_count': len(recent),
                    'imu1': {
                        'gyro': {'x': g1.x, 'y': g1.y, 'z': g1.z},
                        'accel': {'x': a1.x, 'y': a1.y, 'z': a1.z}
                    },
                    'imu2': {
                        'gyro': {'x': g2.x, 'y': g2.y, 'z': g2.z},
                        'accel': {'x': a2.x, 'y': a2.y, 'z': a2.z}
                    }
                }
                result = json.dumps(payload)
                resp = 'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\nContent-Length: {length}\r\n\r\n{body}'.format(length=len(result), body=result)
                try:
                    conn.send(resp.encode('utf-8'))
                except Exception:
                    pass
            except Exception as e:
                err = json.dumps({'status': 'error', 'message': str(e)})
                resp = 'HTTP/1.0 500 Internal Server Error\r\nContent-Type: application/json\r\nContent-Length: {length}\r\n\r\n{body}'.format(length=len(err), body=err)
                try:
                    conn.send(resp.encode('utf-8'))
                except Exception:
                    pass
            conn.close()
            return
        
        # POST /press - handle button presses from the web UI
        if method == 'POST' and path == '/press':
            split_at = text.split('\r\n\r\n', 1)
            body_text = split_at[1] if len(split_at) > 1 else ''
            label = None
            try:
                data = json.loads(body_text)
                label = data.get('button')
            except Exception:
                pass
            
            if not label:
                resp = 'HTTP/1.0 400 Bad Request\r\nContent-Type: application/json\r\nContent-Length: 28\r\n\r\n{"status":"error","message":"no button"}'
                conn.send(resp.encode('utf-8'))
                conn.close()
                return
            
            # Handle the button press
            print(f'[HTTP] Button pressed: {label}')
            current_mode = label.lower().strip()
            
            # Respond with OK
            result = json.dumps({'status': 'ok', 'pressed': label, 'mode': current_mode})
            resp = f'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(result)}\r\n\r\n{result}'
            conn.send(resp.encode('utf-8'))
            conn.close()
            return
        
        # Default 404
        body = '<h1>Not Found</h1>'
        resp = f'HTTP/1.0 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: {len(body)}\r\n\r\n{body}'
        conn.send(resp.encode('utf-8'))
        conn.close()
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        print('[HTTP] Error:', e)

#Finger States
Finger1x = 0
Finger1y = 0
Finger1z = 0

Finger2x = 0
Finger2y = 0
Finger2z = 0


#Sets of I2C
I2C1 = I2C(0, sda=Pin(0), scl=Pin(1))
I2C2 =  I2C(1, sda=Pin(2), scl=Pin(3))

#Sets of MPU6050
imu1 = MPU6050(I2C1)
imu2 = MPU6050(I2C2)

# Start the HTTP server
start_http_server()

while True:
    note_playing = False
    
    # Check for incoming HTTP connections (non-blocking)
    if web_sock is not None:
        try:
            conn, addr = web_sock.accept()
            handle_http_request(conn, addr)
        except Exception:
            pass
    
    # reading values
    gyroscope1 = imu1.gyro
    gyroscope2 = imu2.gyro
    
    
    
    #Turning On Button
    if button.value() == 1:
        if state == 0:
            print("Turn On!")
            state = 1
            StateLed.value(1)
            sleep(1)
        elif state == 1:
            print("Turn Off!")
            state = 0
            StateLed.value(0)
            sleep(1)
    elif state == 0:
        StateLed.value(0)
        

    if state == 1:
        
#         print("1 X =", gyroscope1.x)
#         print("1 Y =", gyroscope1.y)
#         print("1 X =", gyroscope1.x)
#         print("1 Y =", gyroscope1.y)
#         print("1 temp=",imu1.temperature)
#         print("2 temp=",imu2.temperature)
        # Finger1 Functions

        #Rotation X
        if gyroscope1.x < -50 and Finger1x == 0:
            print("Finger1 down")
            Finger1x = 1

            #Note C
            print("(C)")
            sleep(1)
            playtone(tones['C4'])
            note_playing = True
            
        if gyroscope1.x > 50 and Finger1x == 1:
            print("Finger1 up")
            Finger1x = 0

            #Note D
            print("(D)")
            sleep(1)
            playtone(tones['D5'])
            note_playing = True

        #Rotation Y
        if gyroscope1.y < -50 and Finger1y == 0:
            print("Finger1 down")
            Finger1y = 1

            #Note G
            print("(G)")
            sleep(1)
            playtone(tones['G4'])
            note_playing = True
            
        elif gyroscope1.y > 50 and Finger1y == 1:
            print("Finger1 up")
            Finger1y = 0

            #Note A
            print("(A)")
            sleep(1)
            playtone(tones['A4'])
            note_playing = True

        #Rotation Z

                
        #Finger2 Functions

        #Rotation X
        if gyroscope2.x < -50 and Finger2x == 0:
            print("Finger2 down")
            Finger2x = 1
            
            #Note E
            print("(E)")
            sleep(1)
            playtone(tones['E4'])
            note_playing = True

        elif gyroscope2.x > 50 and Finger2x == 1:
            print("Finger2 up")
            Finger2x = 0
            
            #Note F
            print("(F)")
            sleep(1)
            playtone(tones['F4'])
            note_playing = True

        #Rotation Y
        if gyroscope2.y < -50 and Finger2y == 0:
            print("Finger2 down")
            Finger2y = 1

            #Note B
            print("(B)")
            sleep(1)
            playtone(tones['B4'])
            note_playing = True
            
        elif gyroscope2.y > 50 and Finger2y == 1:
            print("Finger2 up")
            Finger1y = 0

            

        #Rotation Z
        
        #Stops Note Playing
        if not note_playing:  # If no button is pressed
            bequiet()
            sleep(0.1) 

        sleep(0.2)


