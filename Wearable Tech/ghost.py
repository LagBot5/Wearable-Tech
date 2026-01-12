"""
Motor Car Controller for MicroPython
Controls motors to drive a robot car via WiFi commands
Compatible with L298N or similar motor drivers
"""

from machine import Pin, PWM
from utime import sleep
import network
import socket
try:
    import ujson as json
except:
    import json

ssid = "THIRDEARTH"
pw = "Mr.LamYo"
#ssid = "BELL470"
#pw = "911A9DEC7146"

class MotorCar:
    """
    Robot car with dual motor control
    
    Pin Configuration:
    - Motor A (Left): IN1, IN2, ENA (PWM)
    - Motor B (Right): IN3, IN4, ENB (PWM)
    """
    
    def __init__(self, in1_pin=16, in2_pin=17, ena_pin=18,
                 in3_pin=19, in4_pin=20, enb_pin=21):
        # Motor A (Left side)
        self.motor_a_in1 = Pin(in1_pin, Pin.OUT)
        self.motor_a_in2 = Pin(in2_pin, Pin.OUT)
        self.motor_a_pwm = PWM(Pin(ena_pin))
        self.motor_a_pwm.freq(1000)
        
        # Motor B (Right side)
        self.motor_b_in1 = Pin(in3_pin, Pin.OUT)
        self.motor_b_in2 = Pin(in4_pin, Pin.OUT)
        self.motor_b_pwm = PWM(Pin(enb_pin))
        self.motor_b_pwm.freq(1000)
        
        self.max_speed = 65535  # 16-bit PWM
        self.current_speed = 0
        
        print("Motor Car initialized")
        self.stop()
    
    def set_motor_a(self, speed):
        """Control Motor A (Left): speed from -100 to 100"""
        if speed > 0:
            self.motor_a_in1.value(1)
            self.motor_a_in2.value(0)
            duty = int((speed / 100) * self.max_speed)
        elif speed < 0:
            self.motor_a_in1.value(0)
            self.motor_a_in2.value(1)
            duty = int((-speed / 100) * self.max_speed)
        else:
            self.motor_a_in1.value(0)
            self.motor_a_in2.value(0)
            duty = 0
        
        self.motor_a_pwm.duty_u16(duty)
    
    def set_motor_b(self, speed):
        """Control Motor B (Right): speed from -100 to 100"""
        if speed > 0:
            self.motor_b_in1.value(1)
            self.motor_b_in2.value(0)
            duty = int((speed / 100) * self.max_speed)
        elif speed < 0:
            self.motor_b_in1.value(0)
            self.motor_b_in2.value(1)
            duty = int((-speed / 100) * self.max_speed)
        else:
            self.motor_b_in1.value(0)
            self.motor_b_in2.value(0)
            duty = 0
        
        self.motor_b_pwm.duty_u16(duty)
    
    def forward(self, speed=70):
        """Drive forward at given speed (0-100)"""
        print(f"Forward: {speed}%")
        self.set_motor_a(speed)
        self.set_motor_b(speed)
        self.current_speed = speed
    
    def backward(self, speed=70):
        """Drive backward at given speed (0-100)"""
        print(f"Backward: {speed}%")
        self.set_motor_a(-speed)
        self.set_motor_b(-speed)
        self.current_speed = -speed
    
    def turn_left(self, speed=60):
        """Turn left (left motor slower/backward, right motor forward)"""
        print(f"Turn Left: {speed}%")
        self.set_motor_a(speed // 2)
        self.set_motor_b(speed)
    
    def turn_right(self, speed=60):
        """Turn right (right motor slower/backward, left motor forward)"""
        print(f"Turn Right: {speed}%")
        self.set_motor_a(speed)
        self.set_motor_b(speed // 2)
    
    def spin_left(self, speed=50):
        """Spin left in place"""
        print(f"Spin Left: {speed}%")
        self.set_motor_a(-speed)
        self.set_motor_b(speed)
    
    def spin_right(self, speed=50):
        """Spin right in place"""
        print(f"Spin Right: {speed}%")
        self.set_motor_a(speed)
        self.set_motor_b(-speed)
    
    def stop(self):
        """Stop all motors"""
        print("Stop")
        self.set_motor_a(0)
        self.set_motor_b(0)
        self.current_speed = 0
    
    def cleanup(self):
        """Clean up PWM and stop motors"""
        self.stop()
        self.motor_a_pwm.deinit()
        self.motor_b_pwm.deinit()


def demo_drive():
    """Demo showing car movements"""
    car = MotorCar()
    
    try:
        print("\n=== Car Demo Started ===\n")
        
        # Forward
        print("Moving forward...")
        car.forward(60)
        sleep(2)
        
        # Turn right
        print("Turning right...")
        car.turn_right(60)
        sleep(1)
        
        # Forward again
        print("Moving forward...")
        car.forward(60)
        sleep(2)
        
        # Turn left
        print("Turning left...")
        car.turn_left(60)
        sleep(1)
        
        # Spin right
        print("Spinning right...")
        car.spin_right(50)
        sleep(1)
        
        # Backward
        print("Moving backward...")
        car.backward(60)
        sleep(2)
        
        # Stop
        car.stop()
        sleep(1)
        
        print("\n=== Demo Complete ===\n")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        car.cleanup()


# Example of integrating with web control
def handle_car_command(car, command, speed=70):
    """
    Handle commands from web controller or other input
    
    Commands: 'forward', 'backward', 'left', 'right', 
              'spin_left', 'spin_right', 'stop'
    """
    command = command.lower()
    
    if command == 'forward':
        car.forward(speed)
    elif command == 'backward':
        car.backward(speed)
    elif command == 'left':
        car.turn_left(speed)
    elif command == 'right':
        car.turn_right(speed)
    elif command == 'spin_left':
        car.spin_left(speed)
    elif command == 'spin_right':
        car.spin_right(speed)
    elif command == 'stop':
        car.stop()
    else:
        print(f"Unknown command: {command}")


def setup_wifi_client(ssid, password):
    """Connect to existing WiFi network to receive commands"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        
        # Wait for connection
        timeout = 30
        start = 0
        while not wlan.isconnected() and start < timeout:
            sleep(1)
            start += 1
            print(f'Connecting... ({start}/{timeout})')
    
    if wlan.isconnected():
        ip_info = wlan.ifconfig()
        print('\n' + '='*50)
        print('🚗 GHOST CAR - NETWORK CONNECTED! ✓')
        print('='*50)
        print(f'  Network SSID: {ssid}')
        print(f'  🌐 IP Address: {ip_info[0]}')
        print(f'  📡 Gateway: {ip_info[2]}')
        print(f'  🔌 Port: 8080')
        print(f'  ✅ Status: READY TO RECEIVE COMMANDS')
        print('='*50)
        print(f'📝 Configuration:')
        print(f'   Set car_ip = "{ip_info[0]}" in main.py')
        print('='*50 + '\n')
        print('🎮 Waiting for gyroscope commands...')
        print('   Ready to receive: forward, backward, left, right, stop\n')
        return wlan
    else:
        print('❌ Failed to connect to WiFi!')
        print('   Check SSID and password')
        return None


def run_car_server():
    """Main server loop - receives gyro commands and drives car"""
    car = MotorCar()
    
    # Connect to WiFi
    wlan = setup_wifi_client()
    if wlan is None:
        print("Cannot start without WiFi connection!")
        return
    
    # Create socket server
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    s.settimeout(0.1)  # Non-blocking
    
    print('\n' + '='*50)
    print('🎯 SERVER STARTED - READY TO RECEIVE COMMANDS')
    print('='*50)
    print('📡 Listening on: 0.0.0.0:8080')
    print('🔄 Server Mode: Non-blocking')
    print('✅ Ghost car is ready for network control!')
    print('='*50 + '\n')
    
    current_direction = 'stop'
    
    try:
        while True:
            try:
                conn, addr = s.accept()
                print(f'Connection from {addr}')
                conn.settimeout(5.0)
                
                try:
                    data = conn.recv(1024)
                    if data:
                        try:
                            # Parse JSON command
                            cmd = json.loads(data.decode('utf-8'))
                            direction = cmd.get('direction', 'stop')
                            speed = cmd.get('speed', 70)
                            
                            # Log received command with visual indicators
                            print('\n' + '-'*50)
                            print(f'📥 COMMAND RECEIVED from {addr[0]}')
                            print(f'   Raw data: {data.decode("utf-8")}')
                            print(f'   Direction: {direction.upper()}')
                            print(f'   Speed: {speed}%')
                            
                            # Execute command
                            if direction != current_direction:
                                # Map direction to emoji
                                direction_emoji = {
                                    'forward': '⬆️',
                                    'backward': '⬇️',
                                    'left': '⬅️',
                                    'right': '➡️',
                                    'spin_left': '↪️',
                                    'spin_right': '↩️',
                                    'stop': '🛑'
                                }
                                emoji = direction_emoji.get(direction, '🤖')
                                
                                print(f'🚗 EXECUTING: {emoji} {direction.upper()}')
                                
                                if direction == 'forward':
                                    car.forward(speed)
                                elif direction == 'backward':
                                    car.backward(speed)
                                elif direction == 'left':
                                    car.turn_left(speed)
                                elif direction == 'right':
                                    car.turn_right(speed)
                                elif direction == 'spin_left':
                                    car.spin_left(speed)
                                elif direction == 'spin_right':
                                    car.spin_right(speed)
                                else:
                                    car.stop()
                                
                                current_direction = direction
                                print(f'✅ Command executed successfully')
                            else:
                                print(f'⚠️ Already executing: {direction}')
                            
                            print('-'*50 + '\n')
                            
                            # Send ACK
                            response = json.dumps({'status': 'ok', 'direction': direction})
                            conn.send(response.encode('utf-8'))
                            print(f'📤 ACK sent to {addr[0]}')
                            
                        except Exception as e:
                            print(f"❌ Command parsing error: {e}")
                            print(f"   Raw data received: {data}")
                            
                except Exception as e:
                    print(f"⚠️ Receive error: {e}")
                finally:
                    conn.close()
                    print(f'🔌 Connection closed with {addr[0]}\n')
                    
            except OSError:
                # Timeout - no connection
                pass
            
            sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        car.cleanup()
        s.close()
        wlan.active(False)
        print("Car server stopped")


if __name__ == "__main__":
    # Run WiFi-controlled car server
    run_car_server()
