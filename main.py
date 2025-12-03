from imu import MPU6050
from utime import sleep, ticks_ms
from machine import Pin, I2C, PWM
import FingerLogic, Tones

button = Pin(16, Pin.IN, Pin.PULL_DOWN)
StateLed = Pin(17, Pin.OUT)
state = 0
turnedOff = True

modeCycleButton = Pin(15, Pin.IN, Pin.PULL_DOWN)
turnedOffA = True

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
mode = 0

def printData():
    print("1 X =", gyroscope1.x)
    print("1 Y =", gyroscope1.y)
    print("2 X =", gyroscope2.x)
    print("2 Y =", gyroscope2.y)
    print("1 temp=",imu1.temperature)
    print("2 temp=",imu2.temperature)



while True:
    # short term mode cycling button
    if modeCycleButton.value() == 1:
        if turnedOffA == True:
            turnedOffA = False
            mode += 1
            if mode >= 4:
                mode = 0
    elif modeCycleButton.value() == 0:
        turnedOffA = True

    note_playing = False
    
    # reading values
    gyroscope1 = imu1.gyro
    accel1 = imu1.accel
    gyroscope2 = imu2.gyro
    accel2 = imu2.accel
    
    #Turning On Button
#    if button.value() == 1:
#        if state == 0:
#            print("Turn On!")
#            state = 1
#            StateLed.value(1)
#            sleep(1)
#        elif state == 1:
#            print("Turn Off!")
#            state = 0
#            StateLed.value(0)
#            sleep(1)
#    elif state == 0:
#        StateLed.value(0)
    if button.value() == 1:
        if turnedOff == True:
            turnedOff = False
            state += 1
            if state >= 2:
                print("Turn Off!")
                state = 0
                StateLed.value(0)
            elif state == 1:
                print("Turn On!")
                StateLed.value(1)
    elif button.value() == 0:
        turnedOff = True
        

    if state == 1:
        #printData() # <-- working function
        FingerLogic.checkFingers(gyroscope1, accel1, gyroscope2, accel2, mode)
        #print(accel1.x, accel1.y, accel1.z)

        #Stops Note Playing
        if not note_playing:  # If no button is pressed
            Tones.bequiet()
    sleep(0.001)
