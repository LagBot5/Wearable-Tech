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

#Declare Modes Again
music = 0
combat = 1
gestures = 2

def checkFingers(gyroscope1, accel1, gyroscope2, accel2, mode):
    global Finger1x, Finger1y, Finger2x, Finger2y
    # Finger 1
    # X Rotation
    if gyroscope1.x < -50 and Finger1x == 0:
        Finger1x = 1
        doAction("finger1x down", mode)

    elif gyroscope1.x > 50 and Finger1x == 1:
        Finger1x = 0
        doAction("finger1x up", mode)

    # Y Rotation
    if gyroscope1.y < -50 and Finger1y == 0:
        Finger1y = 1
        doAction("finger1y down", mode)
    elif gyroscope1.y > 50 and Finger1y == 1:
        Finger1y = 0
        doAction("finger1y up", mode)

    # Finger 2
    # X Rotation
    if gyroscope2.x < -50 and Finger2x == 0:
        Finger2x = 1
        doAction("finger2x down", mode)
    elif gyroscope2.x > 50 and Finger2x == 1:
        Finger2x = 0
        doAction("finger2x up", mode)

    # Y Rotation
    if gyroscope2.y < -50 and Finger2y == 0:
        Finger2y = 1
        doAction("finger2y down", mode)
    elif gyroscope2.y > 50 and Finger2y == 1:
        Finger2y = 0
        doAction("finger2y up", mode)

def doAction(action, mode):
    tones = setupTones()
    if mode == music:
        #Finger1x
        if action == "finger1x down":
            #Note C
            print("(C)")
            sleep(1)
            playtone(tones['C4'])
            note_playing = True
        elif action == "finger1x up":
            #Note D
            print("(D)")
            sleep(1)
            playtone(tones['D4'])
            note_playing = True

        #Finger1y
        elif action == "finger1y down":
            #Note G
            print("(G)")
            sleep(1)
            playtone(tones['G4'])
            note_playing = True
        elif action == "finger1y up":
            #Note A
            print("(A)")
            sleep(1)
            playtone(tones['A4'])
            note_playing = True

        #Finger2x
        elif action == "finger2x down":
            #Note E
            print("(E)")
            sleep(1)
            playtone(tones['E4'])
            note_playing = True
        elif action == "finger2x up":
            #Note F
            print("(F)")
            sleep(1)
            playtone(tones['F4'])
            note_playing = True

        #Finger2y
        elif action == "finger2y down":
            #Note B
            print("(B)")
            sleep(1)
            playtone(tones['B4'])
            note_playing = True
        elif action == "finger2y up":
            #Does nothing rn
            return

    elif mode == combat:
        #Finger1x
        if action == "finger1x down":
            print("combat 1x down")
        elif action == "finger1x up":
            print("combat 1x up")

        #Finger1y
        elif action == "finger1y down":
            print("combat 1y down")
        elif action == "finger1y up":
            print("combat 1y up")

        #Finger2x
        elif action == "finger2x down":
            print("combat 2x down")
        elif action == "finger2x up":
            print("combat 2x up")

        #Finger2y
        elif action == "finger2y down":
            print("combat 2y down")
        elif action == "finger2y up":
            print("combat 2y up")

    elif mode == gestures:
        #Finger1x
        if action == "finger1x down":
            print("gesture 1x down")
        elif action == "finger1x up":
            print("gesture 1x up")

        #Finger1y
        elif action == "finger1y down":
            print("gesture 1y down")
        elif action == "finger1y up":
            print("gesture 1y up")

        #Finger2x
        elif action == "finger2x down":
            print("gesture 2x down")
        elif action == "finger2x up":
            print("gesture 2x up")

        #Finger2y
        elif action == "finger2y down":
            print("gesture 2y down")
        elif action == "finger2y up":
            print("gesture 2y up")
