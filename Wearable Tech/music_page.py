"""
MUSIC MODE
Handles musical note playing based on gyroscope movements
"""

def handle_music_mode(gyroscope1, gyroscope2, Finger1x, Finger1y, Finger2x, Finger2y, process_action):
    """
    Music mode handler - detects finger movements and plays notes
    Returns: (note_playing, Finger1x, Finger1y, Finger2x, Finger2y)
    """
    note_playing = False
    
    # Finger1 Functions
    # Rotation X
    if gyroscope1.x < -50 and Finger1x == 0:
        print("Finger1 down")
        Finger1x = 1
        if process_action('down1x'):
            note_playing = True

    if gyroscope1.x > 50 and Finger1x == 1:
        print("Finger1 up")
        Finger1x = 0
        if process_action('up1x'):
            note_playing = True

    # Rotation Y
    if gyroscope1.y < -50 and Finger1y == 0:
        print("Finger1 down")
        Finger1y = 1
        if process_action('down1y'):
            note_playing = True
    
    elif gyroscope1.y > 50 and Finger1y == 1:
        print("Finger1 up")
        Finger1y = 0
        if process_action('up1y'):
            note_playing = True

    # Finger2 Functions
    # Rotation X
    if gyroscope2.x < -50 and Finger2x == 0:
        print("Finger2 down")
        Finger2x = 1
        if process_action('down2x'):
            note_playing = True

    elif gyroscope2.x > 50 and Finger2x == 1:
        print("Finger2 up")
        Finger2x = 0
        if process_action('up2x'):
            note_playing = True

    # Rotation Y
    if gyroscope2.y < -50 and Finger2y == 0:
        print("Finger2 down")
        Finger2y = 1
        if process_action('down2y'):
            note_playing = True
    
    elif gyroscope2.y > 50 and Finger2y == 1:
        print("Finger2 up")
        Finger2y = 0
        if process_action('up2y'):
            note_playing = True
    
    return note_playing, Finger1x, Finger1y, Finger2x, Finger2y
