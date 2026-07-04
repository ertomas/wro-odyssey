# main.py  (RECUPERADOR)
# ---------------------------------------------------------------------------
# ROBOT RECUPERADOR
#
# Escucha el canal BLE. Cuando el explorador le transmite la posicion del
# objeto (x, y, clase), navega hasta ahi con su propia odometria, cierra la
# garra para agarrar el objeto y vuelve al origen.
#
# Origen acordado: ambos robots arrancan en (0, 0) mirando hacia +x (0 grados).
# El recuperador tiene que arrancar en el MISMO origen que el explorador para
# que las coordenadas signifiquen lo mismo.
#
# Todos los parametros ajustables estan en config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait
from umath import atan2, degrees, sqrt

import config

# El canal tiene que ser el mismo que transmite el explorador.
hub = PrimeHub(observe_channels=[config.CANAL])

motor_izq = Motor(config.PUERTO_MOTOR_IZQ, config.DIRECCION_MOTOR_IZQ)
motor_der = Motor(config.PUERTO_MOTOR_DER, config.DIRECCION_MOTOR_DER)
robot = DriveBase(
    motor_izq, motor_der,
    wheel_diameter=config.WHEEL_DIAMETER,
    axle_track=config.AXLE_TRACK,
)

# Garra: motor que abre/cierra la pinza.
garra = Motor(config.PUERTO_GARRA)

hub.display.char("R")  # "R" de Recuperador

# --- 1. Esperar la coordenada del explorador ---
objetivo = None
while objetivo is None:
    objetivo = hub.ble.observe(config.CANAL)  # None si no oye nada hace ~1 s
    wait(50)

tx, ty, clase = objetivo
hub.speaker.beep()

# --- 2. Navegar desde el origen hacia (tx, ty) ---
robot.reset()
rumbo = degrees(atan2(ty, tx))     # angulo hacia el objetivo
distancia = sqrt(tx * tx + ty * ty)
robot.turn(rumbo)
robot.straight(distancia)

# --- 3. Recuperar: cerrar la garra ---
hub.display.char("G")
# run_until_stalled cierra la pinza hasta que encuentra resistencia (el objeto).
garra.run_until_stalled(config.GARRA_VELOCIDAD, duty_limit=config.GARRA_DUTY_LIMIT)
hub.speaker.beep(frequency=880, duration=400)

# --- 4. Volver al origen con el objeto ---
robot.straight(-distancia)
robot.turn(-rumbo)
hub.display.char("F")  # "F" de Fin
