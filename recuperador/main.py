# main.py  (RECUPERADOR)
# ---------------------------------------------------------------------------
# ROBOT RECUPERADOR
#
# Escucha el canal BLE. Cuando el explorador le transmite la posicion del objeto
# (x, y, clase), navega hasta ahi con su propia odometria, CONFIRMA con el
# ultrasonido que el objeto quedo al alcance de la garra (y corrige el avance
# final si hace falta), lo AGARRA (baja, cierra y lo levanta) y vuelve al origen
# para soltarlo.
#
# HARDWARE:
#   - Port.A / Port.B: ruedas (ver config).
#   - Port.C: garra que ABRE/CIERRA. En ESTE robot abre con velocidad + y cierra
#     con velocidad -. Tras cerrar se mantiene el apriete con dc() (si no, coast
#     = suelta la fuerza).
#   - Port.D: elevador que SUBE/BAJA la garra. En reposo queda ABAJO (cero). La
#     garra arranca y termina ABAJO; sube SOLO despues de agarrar el objeto.
#   - Port.E: ultrasonido, a ~7 cm del punto de agarre.
#
# Origen acordado: ambos robots arrancan en (0, 0) mirando hacia +x (0 grados),
# en el MISMO punto (ver docs/contrato-datos.md). Si el recuperador arranca
# corrido respecto del explorador, se compensa con config.OFFSET_X / OFFSET_Y.
#
# Todos los parametros ajustables estan en config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, UltrasonicSensor
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

garra = Motor(config.PUERTO_GARRA)               # abre/cierra la pinza
elevador = Motor(config.PUERTO_ELEVADOR)         # sube/baja la garra
ultrasonido = UltrasonicSensor(config.PUERTO_ULTRASONIDO)

hub.display.char("R")  # "R" de Recuperador (antes de mover motores: si se traba,
                       # sabemos que fue un movimiento y no la deteccion de puertos)

# --- Arrancar "abierta y abajo" ---
# El elevador arranca en reposo (abajo): fijamos ese punto como cero y solo
# abrimos la garra. Se MANTIENE ABAJO; recien sube DESPUES de agarrar el objeto.
elevador.reset_angle(0)
garra.run_until_stalled(config.GARRA_VELOCIDAD, duty_limit=config.GARRA_DUTY_LIMIT)  # abrir

# --- 1. Esperar la coordenada del explorador ---
objetivo = None
while objetivo is None:
    objetivo = hub.ble.observe(config.CANAL)  # None si no oye nada hace ~1 s
    wait(50)

tx, ty, clase = objetivo
hub.speaker.beep()

# --- 2. Pasar el objetivo al marco propio y navegar ---
# Con offset 0 el objetivo es directo; si el recuperador arranca corrido, se le
# resta el offset para que el punto fisico sea el mismo para ambos robots.
tx_local = tx - config.OFFSET_X
ty_local = ty - config.OFFSET_Y
print("Objetivo x=%d y=%d -> local x=%d y=%d" % (tx, ty, tx_local, ty_local))

robot.reset()
rumbo = degrees(atan2(ty_local, tx_local))
dist = sqrt(tx_local * tx_local + ty_local * ty_local)
robot.turn(rumbo)
robot.straight(dist)

# --- 3. Confirmar con el ultrasonido y corregir el avance final ---
# El objeto deberia leerse en ~DIST_AGARRE. Si esta un poco lejos/cerca, avanzamos
# o retrocedemos en pasos chicos hasta entrar en rango. Acumulamos el avance real
# en avance_total para poder volver exacto al origen despues.
avance_total = dist
en_rango = False
for intento in range(config.INTENTOS_AGARRE):
    d = ultrasonido.distance()
    print("Ultrasonido %d: %d mm" % (intento, d))
    if d > config.DIST_SIN_OBJETO:         # no ve nada -> reintentar (puede ser ruido)
        wait(100)
        continue
    error = d - config.DIST_AGARRE         # >0 objeto lejos, <0 objeto muy cerca
    if abs(error) <= config.TOLERANCIA_AGARRE:
        en_rango = True
        break
    # Corregir avanzando (+) o retrocediendo (-), sin pasarse de PASO_CORRECCION.
    paso = config.PASO_CORRECCION
    if error < 0:
        paso = -config.PASO_CORRECCION
    if abs(error) < config.PASO_CORRECCION:
        paso = error
    robot.straight(paso)
    avance_total += paso
    wait(100)                              # dejar asentar la proxima lectura

# --- 4. Agarrar solo si confirmamos el objeto en rango ---
# Secuencia: ABRIR -> BAJAR -> CERRAR -> SOSTENER -> SUBIR. Se abre ANTES de bajar
# para que la garra descienda abierta y rodee el objeto en vez de golpearlo.
if en_rango:
    hub.display.char("G")  # "G" de Garra
    garra.run_until_stalled(config.GARRA_VELOCIDAD, duty_limit=config.GARRA_DUTY_LIMIT)   # abrir
    elevador.run_target(config.ELEVADOR_VELOCIDAD, 0)  # asegurar abajo (ya abierta, no golpea)
    garra.run_until_stalled(-config.GARRA_VELOCIDAD, duty_limit=config.GARRA_DUTY_LIMIT)  # cerrar
    garra.dc(-config.GARRA_DUTY_SOSTEN)  # seguir apretando para no soltar al moverse
    elevador.run_target(config.ELEVADOR_VELOCIDAD, config.ELEVADOR_ANGULO_ARRIBA)  # subir con el objeto
    hub.speaker.beep(frequency=880, duration=400)
else:
    # No se pudo confirmar objeto al alcance: avisar y no cerrar la garra.
    hub.display.char("X")
    hub.speaker.beep(frequency=220, duration=600)

# --- 5. Volver al origen (compensando las correcciones del paso 3) ---
robot.straight(-avance_total)
robot.turn(-rumbo)

# --- 6. Soltar el objeto (si lo agarramos) y dejar la garra en la posicion
#        inicial: elevador ABAJO (cero de reposo). ---
if en_rango:
    hub.display.char("A")  # "A" de Abrir
    elevador.run_target(config.ELEVADOR_VELOCIDAD, 0)  # bajar
    garra.run_until_stalled(config.GARRA_VELOCIDAD, duty_limit=config.GARRA_DUTY_LIMIT)  # abrir/soltar
else:
    elevador.run_target(config.ELEVADOR_VELOCIDAD, 0)  # bajar a la posicion inicial

hub.display.char("F")  # "F" de Fin
