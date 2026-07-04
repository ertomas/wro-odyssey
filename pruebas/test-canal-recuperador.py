# test-canal-recuperador.py
# ---------------------------------------------------------------------------
# DEMO SIMPLE DE CANAL (2 de 2)
#
# Escucha el canal BLE y, al recibir una coordenada (x, y, clase), maneja
# hacia ella UNA vez. Sirve para confirmar que broadcast/observe + la
# navegacion basica funcionan, antes de armar la mision completa.
#
# Origen: el robot arranca en (0, 0) mirando hacia +x (adelante = 0 grados).
# Ajusta wheel_diameter y axle_track segun TU robot (ver docs/calibracion.md).
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait
from umath import atan2, degrees, sqrt

# El canal (1) tiene que ser el mismo que transmite el explorador.
hub = PrimeHub(observe_channels=[1])

motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.A)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=112)

hub.display.char("R")  # "R" de Recuperador

# Esperar hasta recibir una coordenada.
objetivo = None
while objetivo is None:
    objetivo = hub.ble.observe(1)  # None si no oye nada hace ~1 segundo
    wait(50)

x, y, clase = objetivo
hub.speaker.beep()

# Navegar al punto: girar hacia el y avanzar la distancia en linea recta.
robot.reset()
rumbo = degrees(atan2(y, x))       # angulo hacia el objetivo
distancia = sqrt(x * x + y * y)    # distancia en linea recta (mm)
robot.turn(rumbo)
robot.straight(distancia)

# Llegamos.
hub.speaker.beep(frequency=880, duration=400)
hub.display.char("F")  # "F" de Fin
