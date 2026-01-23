
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

class MotorCar:
    """
    Robot car with dual motor control
    
    Pin Configuration:
    - Motor A (Left): IN1, IN2, ENA (PWM)
    - Motor B (Right): IN3, IN4, ENB (PWM)
    """
    
    def __init__(self, in1_pin=16, in2_pin=17, ena_pin=18,
                 in3_pin=19, in4_pin=20, enb_pin=21, servo1_pin=22, servo2_pin=26):
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
        
        # Servo 1 (Left side) for attacks
        self.servo1 = None
        try:
            self.servo1 = PWM(Pin(servo1_pin))
            self.servo1.freq(50)  # 50Hz for servo control
            print("Servo 1 initialized on pin", servo1_pin)
        except Exception as e:
            print(f"Servo 1 initialization failed: {e}")
            self.servo1 = None
        
        # Servo 2 (Right side) for attacks - mirrors Servo 1
        self.servo2 = None
        try:
            self.servo2 = PWM(Pin(servo2_pin))
            self.servo2.freq(50)  # 50Hz for servo control
            print("Servo 2 initialized on pin", servo2_pin)
        except Exception as e:
            print(f"Servo 2 initialization failed: {e}")
            self.servo2 = None
        
        # Set both servos to start position
        if self.servo1 or self.servo2:
            self.set_servo_angle(0)  # Start at 0 degrees
        
        self.max_speed = 65535  # 16-bit PWM
        self.current_speed = 0
        self.current_servo_angle = 0
        
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
        self.set_motor_b(speed)
        self.set_motor_a(speed)
        self.current_speed = speed
    
    def backward(self, speed=70):
        """Drive backward at given speed (0-100)"""
        print(f"Backward: {speed}%")
        self.set_motor_b(-speed)
        self.set_motor_a(-speed)
        self.current_speed = -speed
    
    def turn_left(self, speed=60):
        """Turn left (left motor backward, right motor forward)"""
        print(f"Turn Left: {speed}%")
        self.set_motor_b(-speed)
        self.set_motor_a(speed)
    
    def turn_right(self, speed=60):
        """Turn right (left motor forward, right motor backward)"""
        print(f"Turn Right: {speed}%")
        self.set_motor_b(speed)
        self.set_motor_a(-speed)
    
    def spin_left(self, speed=50):
        """Spin left in place"""
        print(f"Spin Left: {speed}%")
        self.set_motor_b(-speed)
        self.set_motor_a(speed)
    
    def spin_right(self, speed=50):
        """Spin right in place"""
        print(f"Spin Right: {speed}%")
        self.set_motor_b(speed)
        self.set_motor_a(-speed)
    
    def stop(self):
        """Stop all motors"""
        print("Stop")
        self.set_motor_a(0)
        self.set_motor_b(0)
        self.current_speed = 0
    
    def set_servo_angle(self, angle):
        """Set both servos to specific angle (0-180 degrees)
        Servo 1 moves to angle, Servo 2 moves to opposite angle (180-angle)
        This creates mirrored movement from opposite sides
        """
        if self.servo1 is None and self.servo2 is None:
            return False
        
        try:
            # Convert angle to duty cycle
            # Servo pulse width: 1ms (0°) to 2ms (180°) at 50Hz
            # Duty cycle range: ~1600 to ~8000 for 16-bit PWM
            min_duty = 1600   # 0 degrees
            max_duty = 8000   # 180 degrees
            
            # Clamp angle between 0 and 180
            angle = max(0, min(180, angle))
            
            # Calculate duty cycle for servo 1
            duty1 = int(min_duty + (angle / 180) * (max_duty - min_duty))
            
            # Calculate opposite angle for servo 2 (mirrored movement)
            opposite_angle = 180 - angle
            duty2 = int(min_duty + (opposite_angle / 180) * (max_duty - min_duty))
            
            # Set servo 1
            if self.servo1:
                self.servo1.duty_u16(duty1)
            
            # Set servo 2 (opposite direction)
            if self.servo2:
                self.servo2.duty_u16(duty2)
            
            self.current_servo_angle = angle
            print(f"Servos angle: {angle}° (Servo2: {opposite_angle}°)")
            return True
        except Exception as e:
            print(f"Servo error: {e}")
            return False
    
    def cleanup(self):
        """Clean up PWM and stop motors"""
        print("Stopping motors and cleaning up...")
        self.stop()
        # Ensure motors are fully off
        self.motor_a_in1.value(0)
        self.motor_a_in2.value(0)
        self.motor_b_in1.value(0)
        self.motor_b_in2.value(0)
        # Deinitialize PWM
        self.motor_a_pwm.deinit()
        self.motor_b_pwm.deinit()
        if self.servo1:
            self.servo1.deinit()
        if self.servo2:
            self.servo2.deinit()
        print("Motors stopped and cleanup complete")


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
     
def setup_wifi_client(ssid="someWifi", password="somePassword"):
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
        print('Car WiFi Connected!')
        print('='*50)
        print(f'  Network: {ssid}')
        print(f'  IP Address: {ip_info[0]}')
        print(f'  Listening on port: 8080')
        print('='*50)
        print(f'Set car_ip = \"{ip_info[0]}\" in main.py')
        print('='*50 + '\n')
        return wlan
    else:
        print('Failed to connect to WiFi!')
        return None


def run_car_client(controller_ip):
    """Main client loop - polls controller for commands and executes them"""
    car = MotorCar()
    
    # Connect to WiFi
    wlan = setup_wifi_client()
    if wlan is None:
        print("Cannot start without WiFi connection!")
        return
    
    print('\n' + '='*50)
    print('🚗 GHOST CAR - CLIENT MODE')
    print('='*50)
    print(f'   Polling controller at: {controller_ip}')
    print(f'   Command endpoint: /car_command')
    print(f'   Poll interval: 100ms')
    print(f'   Safety timeout: 2 seconds')
    print('='*50 + '\n')
    
    current_direction = 'stop'
    last_log_entry = None
    poll_url = f'http://{controller_ip}/car_command'
    consecutive_failures = 0
    max_failures_before_reconnect = 50  # Try to reconnect after 50 failures
    last_command_time = 0
    command_timeout = 2000  # milliseconds - stop if no command for 2 seconds
    error_logged = False  # Track if we've logged connection issues
    
    try:
        while True:
            try:
                # Poll controller for command
                try:
                    import urequests as requests
                except:
                    import requests
                
                response = requests.get(poll_url, timeout=0.5)
                
                if response.status_code == 200:
                    cmd = response.json()
                    direction = cmd.get('direction', 'stop')
                    speed = cmd.get('speed', 70)
                    servo_angle = cmd.get('servo_angle', None)  # Get servo angle if present
                    log_entry = cmd.get('log_entry', None)  # Get latest log entry
                    response.close()
                    
                    # Reset failure counter on success
                    if consecutive_failures > 0:
                        print('[CONNECTION] ✅ Reconnected to controller')
                        error_logged = False
                    consecutive_failures = 0
                    
                    # Update last command time
                    from utime import ticks_ms
                    last_command_time = ticks_ms()
                    
                    # Show log updates from controller
                    if log_entry and log_entry != last_log_entry:
                        print(f'[CONTROLLER LOG] {log_entry}')
                        last_log_entry = log_entry
                    
                    # Control servo if angle is specified
                    if servo_angle is not None and servo_angle != car.current_servo_angle:
                        print(f'[ATTACK] Servo → {servo_angle}°')
                        car.set_servo_angle(servo_angle)
                    
                    # Execute command (always execute to ensure motors respond)
                    if direction != current_direction:
                        print(f'[COMMAND] {direction.upper()} @ {speed}%')
                        current_direction = direction
                    
                    # Execute motor command based on direction
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
                        
                else:
                    response.close()
                    consecutive_failures += 1
                    if not error_logged:
                        print(f'[CONNECTION] ⚠️ Bad response from controller (status: {response.status_code})')
                        error_logged = True
                    
            except Exception as e:
                consecutive_failures += 1
                # Only log first error to avoid spam
                if not error_logged:
                    print(f'[CONNECTION] ⚠️ Cannot reach controller: {str(e)[:50]}')
                    error_logged = True
                
                # Attempt WiFi reconnection if failures are too high
                if consecutive_failures >= max_failures_before_reconnect:
                    print(f'[CONNECTION] ❌ Too many failures ({consecutive_failures}), attempting WiFi reconnect...')
                    try:
                        wlan.active(False)
                        sleep(2)
                        wlan = setup_wifi_client()
                        if wlan:
                            print('[CONNECTION] 🔄 WiFi reconnected, resuming...')
                            consecutive_failures = 0
                            error_logged = False
                        else:
                            print('[CONNECTION] ❌ WiFi reconnect failed, stopping...')
                            break
                    except:
                        print('[CONNECTION] ❌ Reconnect failed, stopping...')
                        break
            
            # Connection timeout - continue last command instead of stopping
            from utime import ticks_ms, ticks_diff
            if last_command_time > 0 and ticks_diff(ticks_ms(), last_command_time) > command_timeout:
                if not error_logged:
                    print('[SAFETY] ⚠️ Connection timeout - continuing last command:', current_direction.upper())
                    error_logged = True
            
            sleep(0.01)  # Poll every 10ms for instant response
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        car.cleanup()
        wlan.active(False)
        print("Ghost car stopped")


if __name__ == "__main__":
    # CONFIGURATION: Set your controller Pico's IP address here
    # Run main.py first and look for the line: "[WIFI] IP Address: X.X.X.X"
    # Copy that IP address and paste it below
    CONTROLLER_IP = 'someIP(999.192.19.09)'  # ⚠️ CHANGE THIS to your main.py controller's IP address!
    
    print('\n' + '='*50)
    print('⚙️  GHOST CAR CONFIGURATION')
    print('='*50)
    print(f'   Controller IP: {CONTROLLER_IP}')
    print(f'   WiFi Network: THIRDEARTH')
    print('='*50)
    print('\n⚠️  Make sure main.py is running first!')
    print('⚠️  Check main.py output for correct IP address\n')
    
    # Run WiFi-controlled car client (polls controller for commands)
    run_car_client(CONTROLLER_IP)


