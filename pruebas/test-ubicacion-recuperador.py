# test-ubicacion-recuperador.py
# ---------------------------------------------------------------------------
# PRUEBA DE UBICACION (2 de 2)
#
# Escucha el canal BLE. Cuando el explorador (test-ubicacion-explorador.py, en
# el otro hub) transmite el sitio (x, y, clase), navega hasta ahi con su propia
# odometria, cierra la garra, vuelve a su origen y abre la garra para soltar.
# Sirve para confirmar odometria + navegacion + garra juntas, sin camara.
#
# POSICION DE ARRANQUE: el recuperador NO arranca en el mismo punto que el
# explorador. Arranca 200 mm a la IZQUIERDA del explorador, mirando en la MISMA
# direccion (+x adelante). Como en Pybricks turn() positivo es horario, en el
# marco del explorador +y apunta a la DERECHA, asi que "izquierda" es -y: el
# recuperador esta en (0, -200) de ese marco. Para navegar en SU propio marco le
# restamos ese offset al objetivo recibido (ver OFFSET_X / OFFSET_Y).
#
# Este archivo es autocontenido (no importa config.py). Los valores de hardware
# de abajo tienen que quedar en SYNC con recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait
from umath import atan2, degrees, sqrt

# --- Parametros de la prueba ---
CANAL = 1                 # el mismo que transmite el explorador
GARRA_VELOCIDAD = 300     # deg/s al mover la pinza
GARRA_DUTY_LIMIT = 50     # % de fuerza al cerrar/abrir

# Posicion del recuperador en el marco del explorador (izquierda = -y).
OFFSET_X = 0              # mm: mismo "adelante" que el explorador
OFFSET_Y = -200          # mm: 20 cm a la izquierda del explorador

# --- Hardware calibrado (mantener en sync con recuperador/config.py) ---
hub = PrimeHub(observe_channels=[CANAL])
motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.A, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=160)
garra = Motor(Port.C)

hub.display.char("R")  # "R" de Recuperador

# --- 1. Esperar la coordenada del explorador ---
objetivo = None
while objetivo is None:
    objetivo = hub.ble.observe(CANAL)  # None si no oye nada hace ~1 s
    wait(50)

tx, ty, clase = objetivo
hub.speaker.beep()

# --- 2. Pasar el objetivo al marco propio y navegar ---
# El explorador mide desde SU origen; el recuperador arranca corrido OFFSET_*,
# asi que resta ese offset para que el punto fisico sea el mismo para ambos.
tx_local = tx - OFFSET_X
ty_local = ty - OFFSET_Y
print("Objetivo x=%d y=%d -> local x=%d y=%d" % (tx, ty, tx_local, ty_local))

robot.reset()
rumbo = degrees(atan2(ty_local, tx_local))
dist = sqrt(tx_local * tx_local + ty_local * ty_local)
robot.turn(rumbo)
robot.straight(dist)

# --- 3. Cerrar la garra (agarrar) ---
hub.display.char("G")  # "G" de Garra
garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)
hub.speaker.beep(frequency=880, duration=400)

# --- 4. Volver a su origen ---
robot.straight(-dist)
robot.turn(-rumbo)

# --- 5. Abrir la garra (soltar) al final del ciclo ---
hub.display.char("A")  # "A" de Abrir
garra.run_until_stalled(-GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)
hub.display.char("F")  # "F" de Fin
