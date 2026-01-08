#pip install djitellopy pygame opencv-python
from djitellopy import Tello
import pygame
import time
import math
import random
import cv2
import numpy as np

# --- Inizializza Pygame e joystick ---
pygame.init()
pygame.joystick.init()

screen = pygame.display.set_mode((1000, 800))
pygame.display.set_caption("Tello Joystick Control")

joystick = pygame.joystick.Joystick(0)
joystick.init()
print("Joystick rilevato:", joystick.get_name())

# --- Connetti Tello ---
tello = Tello()
tello.connect()
battery = tello.get_battery()
print("Batteria iniziale:", battery, "%")
time.sleep(2)  # ritardo per far partire i comandi RC

# --- Impostazioni ---
speed = 50
rotation_speed = 200
DEADZONE = 0.20

airborne = False
tornado_active = False
flip_pressed = False
last_flip_time = 0
last_battery_check = 0
MIN_BATTERY_CAMERA = 30
#camera_active = False

# --- Funzioni ---
def apply_deadzone(value):
    if abs(value) < DEADZONE:
        return 0
    return value

def get_joystick_input():
    pygame.event.pump()
    x = apply_deadzone(joystick.get_axis(0))  # sinistra/destra
    y = apply_deadzone(joystick.get_axis(1))  # avanti/indietro

    lr = int(x * speed)
    fb = int(-y * speed)
    ud = 0
    yv = 0

    # Pulsante 0: verticale/rotazione
    if joystick.get_button(0):
        if abs(y) > abs(x):
            ud = int(-y * speed)
            yv = 0
        else:
            yv = int(x * rotation_speed)
            ud = 0
        lr = 0
        fb = 0

    return lr, fb, ud, yv

# --- Avvia stream telecamera se batteria sufficiente ---
#if battery >= MIN_BATTERY_CAMERA:
    #tello.streamon()
   # camera_active = True
   # time.sleep(2)  # lascia partire il feed
   # print("Telecamera attiva")
#else:
   # print("Batteria troppo bassa per la telecamera (>30% necessario)")

# --- Ciclo principale ---
running = True
while running:
    current_time = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if airborne:
                tello.land()
            tello.end()
            pygame.quit()
            exit()

        elif event.type == pygame.JOYBUTTONDOWN:
            # Flip singolo con pulsante 1
            if airborne and event.button == 1 and not flip_pressed:
                tello.flip('f')
                print("Flip in avanti!")
                flip_pressed = True

            # Decollo con pulsante 4
            elif event.button == 4 and not airborne:
                tello.takeoff()
                airborne = True

            # Atterraggio con pulsante 5
            elif event.button == 5 and airborne:
                tello.land()
                airborne = False
                tornado_active = False

            # Toggle tornado mode con pulsante 2
            elif airborne and event.button == 2:
                tornado_active = not tornado_active
                print(f"Tornado mode {'attivo' if tornado_active else 'disattivo'}")

        elif event.type == pygame.JOYBUTTONUP:
            # Reset flip_pressed al rilascio del pulsante 1
            if event.button == 1:
                flip_pressed = False

    # Leggi joystick
    lr, fb, ud, yv = get_joystick_input()

    # Tornado mode acrobatico
    if tornado_active:
        t = time.time()
        ud = int(10 * math.sin(5 * t))  # oscillazione verticale
        yv = 400                          # rotazione superveloce

    # Invia comandi solo se decollato
    if airborne:
        tello.send_rc_control(lr, fb, ud, yv)

    # Aggiorna feed telecamera
    #if camera_active:
        #frame = tello.get_frame_read().frame
       # if frame is not None:
        #    frame = cv2.resize(frame, (1000, 800))
      #      frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
       #     frame = np.rot90(frame)
       #     frame = np.flip(frame, axis=0)
       #     surf = pygame.surfarray.make_surface(frame)
       #     screen.blit(surf, (0, 0))

    # Controllo batteria ogni 10 secondi
    if current_time - last_battery_check > 10:
        battery = tello.get_battery()
        print(f"Batteria attuale: {battery}%")
        last_battery_check = current_time

        # Disattiva camera se batteria troppo bassa
        #if battery < MIN_BATTERY_CAMERA and camera_active:
            #tello.streamoff()
           # camera_active = False
            #print("Telecamera disattivata: batteria bassa")

        # Riattiva camera se batteria sufficiente
        #elif battery >= MIN_BATTERY_CAMERA and not camera_active:
            #tello.streamon()
            #camera_active = True
            #time.sleep(2)
            #print("Telecamera riattivata: batteria sufficiente")

    pygame.display.update()
    time.sleep(0.05)