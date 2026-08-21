# test-canal-recuperador.py
# ---------------------------------------------------------------------------
# DEMO SIMPLE DE CANAL (2 de 2)
#
# Escucha el canal BLE y, al recibir una coordenada (x, y, clase), maneja
# hacia ella UNA vez. Sirve para confirmar que broadcast/observe + la
# navegacion basica funcionan, antes de armar la mision completa.
#
# No usa garra ni ultrasonido: solo canal + odometria. Si esto no anda, no
# tiene sentido depurar el agarre todavia.
#
# Origen: el robot arranca en (0, 0) mirando hacia +x (adelante = 0 grados).
# No aplica OFFSET: para esta prueba pone el robot en el origen y listo.
#
# Usa BLERadio (pybricks.messaging), la MISMA API que recuperador/main.py.
# Los valores de hardware tienen que quedar en SYNC con recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.messaging import BLERadio
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait
from umath import atan2, degrees, sqrt

# El canal (1) tiene que ser el mismo que transmite el explorador.
CANAL = 1

hub = PrimeHub()
radio = BLERadio(observe_channels=[CANAL])

# --- Hardware calibrado (SYNC con recuperador/config.py) ---
motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.A, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=164)

hub.display.char("R")  # "R" de Recuperador

# Esperar hasta recibir una coordenada VALIDA. Ignoramos cualquier otra cosa que
# aparezca en el canal (p.ej. broadcasts de otro programa) en vez de crashear.
objetivo = None
while objetivo is None:
    datos = radio.observe(CANAL)  # None si no oye nada hace ~1 segundo
    if isinstance(datos, (tuple, list)) and len(datos) == 3:
        objetivo = datos
    elif datos is not None:
        print("BLE ignorado (no es coordenada):", datos)
    wait(50)

x, y, clase = objetivo
print("Objetivo recibido: x=%d y=%d clase=%d" % (x, y, clase))
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
