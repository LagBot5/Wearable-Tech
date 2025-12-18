from imu import MPU6050
from utime import sleep, ticks_ms
from machine import Pin, I2C, PWM
import FingerLogic, Tones

button = Pin(16, Pin.IN, Pin.PULL_DOWN)
StateLed = Pin(17, Pin.OUT)
state = 0
turnedOffB = True

#modeCycleButton = Pin(15, Pin.IN, Pin.PULL_DOWN)
#turnedOffA = True

now = ticks_ms()

#Sets of I2C
I2C1 = I2C(0, sda=Pin(0), scl=Pin(1))
I2C2 =  I2C(1, sda=Pin(2), scl=Pin(3))

#Sets of MPU6050
imu1 = MPU6050(I2C1)
imu2 = MPU6050(I2C2)

#Declare Modes
music = 0
combat = 1
gestures = 2
navigateApp = 3
mode = 0

def printData():
    # MPU 1
    print("1 X Rotation =", gyroscope1.x)
    print("1 Y Rotation =", gyroscope1.y)
    print("1 Z Rotation =", gyroscope1.z)
    print("1 X Speed =", accel1.x)
    print("1 Y Speed =", accel1.y)
    print("1 Z Speed =", accel1.z)
    print("1 temp =",imu1.temperature)
    # MPU 2
    print("2 X Rotaion =", gyroscope2.x)
    print("2 Y Rotaion =", gyroscope2.y)
    print("2 Z Rotaion =", gyroscope2.z)
    print("2 X Speed =", accel2.x)
    print("2 Y Speed =", accel2.y)
    print("2 Z Speed =", accel2.z)
    print("2 temp =",imu2.temperature)
    sleep(1)

while True:
    note_playing = False

    # reading values
    gyroscope1 = imu1.gyro
    accel1 = imu1.accel
    gyroscope2 = imu2.gyro
    accel2 = imu2.accel

    # short term mode cycling button
#    if modeCycleButton.value() == 1:
#        if turnedOffA == True:
#            turnedOffA = False
#            mode += 1
#            if mode >= 4:
#                mode = 0
#            print(mode)
#    elif modeCycleButton.value() == 0:
#        turnedOffA = True

    # Debounced power button
    if button.value() == 1:
        if turnedOffB == True:
            turnedOffB = False
            state += 1
            if state >= 2:
                print("Turn Off!")
                state = 0
                StateLed.value(0)
            elif state == 1:
                print("Turn On!")
                StateLed.value(1)
    elif button.value() == 0:
        turnedOffB = True

    #If power on, do this
    if state == 1:
        #printData() # <-- working function
        FingerLogic.checkFingers(gyroscope1, accel1, gyroscope2, accel2, mode)

        #Stops Note Playing
        if not note_playing:  # If no button is pressed
            Tones.bequiet()
    sleep(0.07)
