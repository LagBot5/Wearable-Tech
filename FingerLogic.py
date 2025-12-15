from imu import MPU6050
from utime import sleep, ticks_ms
from machine import Pin, I2C, PWM
from Tones import playtone, setupTones, playLittleLamb

#Finger States
Finger1x = 0
Finger1y = 0
Finger1z = 0
Fast1x = 0
Fast1y = 0
Fast1z = 0

Finger2x = 0
Finger2y = 0
Finger2z = 0
Fast2x = 0
Fast2y = 0
Fast2z = 0

#Motion History Variables
now = ticks_ms()
lastTimeCheckHistory = ticks_ms()
MotionHistory = []
resetTimerMilliseconds = 7000

#Declare Modes Again
music = 0
combat = 1
gestures = 2
navigateApp = 3

def checkFingers(gyroscope1, accel1, gyroscope2, accel2, mode):
    global Finger1x, Finger1y, Finger2x, Finger2y, Fast1x
    # Finger 1
    # X Rotation
    if gyroscope1.x < -50 and Finger1x == 0:
        Finger1x = 1
        doAction("down1x", mode)

    elif gyroscope1.x > 50 and Finger1x == 1:
        Finger1x = 0
        doAction("up1x", mode)

    # Y Rotation
    if gyroscope1.y < -50 and Finger1y == 0:
        Finger1y = 1
        doAction("down1y", mode)
    elif gyroscope1.y > 50 and Finger1y == 1:
        Finger1y = 0
        doAction("up1y", mode)
    
    # X Acceleration
    if accel1.x < -1 and Fast1x == 0:
        Fast1x = 1
        doAction("left1x", mode)
    elif accel1.x > 1 and Fast1x == 1:
        Fast1x = 0
        doAction("right1x", mode)

    # Finger 2
    # X Rotation
    if gyroscope2.x < -50 and Finger2x == 0:
        Finger2x = 1
        doAction("down2x", mode)
    elif gyroscope2.x > 50 and Finger2x == 1:
        Finger2x = 0
        doAction("up2x", mode)

    # Y Rotation
    if gyroscope2.y < -50 and Finger2y == 0:
        Finger2y = 1
        doAction("down2y", mode)
    elif gyroscope2.y > 50 and Finger2y == 1:
        Finger2y = 0
        doAction("up2y", mode)

def checkHistory(action):
    global MotionHistory, now, lastTimeCheckHistory
    now = ticks_ms()
    millisecondsSinceLastTimeCheckHistory = now - lastTimeCheckHistory
    if len(MotionHistory) >= 4:
        MotionHistory = []
        MotionHistory.append(action)
    elif millisecondsSinceLastTimeCheckHistory > resetTimerMilliseconds:
        lastTimeCheckHistory = now
        MotionHistory = []
        MotionHistory.append(action)
    else:
        MotionHistory.append(action)
        lastTimeCheckHistory = now
    print(MotionHistory)

def doAction(action, mode):
    checkHistory(action)
    tones = setupTones()
    if mode == music:
        #Combo
        if MotionHistory == ["down1x", "down2x", "up2x", "up1x"]:
            playLittleLamb(tones)
        elif MotionHistory == ["down2x", "down1x", "up1x", "up2x"]:
            print('singsong2')

        #Finger1x
        elif action == "down1x":
            #Note C
            print("(C)")
            sleep(1)
            playtone(tones['C4'])
            note_playing = True
        elif action == "up1x":
            #Note D
            print("(D)")
            sleep(1)
            playtone(tones['D4'])
            note_playing = True

        #Finger1y
        elif action == "down1y":
            #Note G
            print("(G)")
            sleep(1)
            playtone(tones['G4'])
            note_playing = True
        elif action == "up1y":
            #Note A
            print("(A)")
            sleep(1)
            playtone(tones['A4'])
            note_playing = True

        #Finger2x
        elif action == "down2x":
            #Note E
            print("(E)")
            sleep(1)
            playtone(tones['E4'])
            note_playing = True
        elif action == "up2x":
            #Note F
            print("(F)")
            sleep(1)
            playtone(tones['F4'])
            note_playing = True

        #Finger2y
        elif action == "down2y":
            #Note B
            print("(B)")
            sleep(1)
            playtone(tones['B4'])
            note_playing = True
        elif action == "up2y":
            #Does nothing rn
            return

    elif mode == combat:
        #Finger1x
        if action == "down1x":
            print("combat 1x down")
        elif action == "up1x":
            print("combat 1x up")

        #Finger1y
        elif action == "down1y":
            print("combat 1y down")
        elif action == "up1y":
            print("combat 1y up")

        #Finger2x
        elif action == "down2x":
            print("combat 2x down")
        elif action == "up2x":
            print("combat 2x up")

        #Finger2y
        elif action == "down2y":
            print("combat 2y down")
        elif action == "up2y":
            print("combat 2y up")

    elif mode == gestures:
        #Combo
        if MotionHistory == ['left1x', 'right1x', 'left1x', 'right1x'] or MotionHistory == ['right1x', 'left1x', 'right1x', 'left1x']:
            print('wave')

        #Finger1x
        if action == "down1x":
            print("gesture 1x down")
        elif action == "up1x":
            print("gesture 1x up")

        #Finger1y
        elif action == "down1y":
            print("gesture 1y down")
        elif action == "up1y":
            print("gesture 1y up")

        #Finger2x
        elif action == "down2x":
            print("gesture 2x down")
        elif action == "up2x":
            print("gesture 2x up")

        #Finger2y
        elif action == "down2y":
            print("gesture 2y down")
        elif action == "up2y":
            print("gesture 2y up")
    
    elif mode == navigateApp:
        #Finger1x
        if action == "down1x":
            print("navigateApp 1x down")
        elif action == "up1x":
            print("navigateApp 1x up")

        #Finger1y
        elif action == "down1y":
            print("navigateApp 1y down")
        elif action == "up1y":
            print("navigateApp 1y up")

        #Finger2x
        elif action == "down2x":
            print("navigateApp 2x down")
        elif action == "up2x":
            print("navigateApp 2x up")

        #Finger2y
        elif action == "down2y":
            print("navigateApp 2y down")
        elif action == "up2y":
            print("navigateApp 2y up")
