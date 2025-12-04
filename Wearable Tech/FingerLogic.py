from imu import MPU6050
from utime import sleep, ticks_ms
from machine import Pin, I2C, PWM
from Tones import playtone, setupTones

#Finger States
Finger1x = 0
Finger1y = 0
Finger1z = 0

Finger2x = 0
Finger2y = 0
Finger2z = 0

def checkFingers(gyroscope1, gyroscope2):
    global Finger1x, Finger1y, Finger2x, Finger2y
    tones = setupTones()
    #speaker = setupSpeaker()

    # Finger 1
    # X Rotation
    if gyroscope1.x < -50 and Finger1x == 0:
        print("Finger1X down")
        Finger1x = 1

        #Note C
        print("(C)")
        sleep(1)
        playtone(tones['C4'])
        note_playing = True
        
    if gyroscope1.x > 50 and Finger1x == 1:
        print("Finger1X up")
        Finger1x = 0

        #Note D
        print("(D)")
        sleep(1)
        playtone(tones['D4'])
        note_playing = True
    
    # Y Rotation
    if gyroscope1.y < -50 and Finger1y == 0:
        print("Finger1Y down")
        Finger1y = 1

        #Note G
        print("(G)")
        sleep(1)
        playtone(tones['G4'])
        note_playing = True
        
    elif gyroscope1.y > 50 and Finger1y == 1:
        print("Finger1Y up")
        Finger1y = 0

        #Note A
        print("(A)")
        sleep(1)
        playtone(tones['A4'])
        note_playing = True

    # Finger 2
    # X Rotation
    if gyroscope2.x < -50 and Finger2x == 0:
        print("Finger2X down")
        Finger2x = 1
        
        #Note E
        print("(E)")
        sleep(1)
        playtone(tones['E4'])
        note_playing = True

    elif gyroscope2.x > 50 and Finger2x == 1:
        print("Finger2X up")
        Finger2x = 0
        
        #Note F
        print("(F)")
        sleep(1)
        playtone(tones['F4'])
        note_playing = True

    # Y Rotation
    if gyroscope2.y < -50 and Finger2y == 0:
        print("Finger2Y down")
        Finger2y = 1

        #Note B
        print("(B)")
        sleep(1)
        playtone(tones['B4'])
        note_playing = True
        
    elif gyroscope2.y > 50 and Finger2y == 1:
        print("Finger2Y up")
        Finger1y = 0