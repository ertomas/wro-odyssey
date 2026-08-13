# main.py  (RECUPERADOR)
# ---------------------------------------------------------------------------
# ROBOT RECUPERADOR
#
# Escucha el canal BLE. Cuando el explorador le transmite la posicion del objeto
# (x, y, clase), navega hasta ahi con su propia odometria, hace la APROXIMACION
# FINAL despacio guiado por el ultrasonido (frena apenas el objeto entra en rango,
# sin embestirlo), lo AGARRA (baja, cierra y lo levanta) y vuelve al origen para
# soltarlo.
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
from pybricks.messaging import BLERadio
from pybricks.tools import wait
from umath import atan2, degrees, sqrt

import config

hub = PrimeHub()
# Mensajeria BLE (firmware nuevo): observar el canal que transmite el explorador.
# El canal tiene que ser el MISMO que broadcastea el explorador.
radio = BLERadio(observe_channels=[config.CANAL])

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

# --- 1. Esperar una coordenada VALIDA del explorador ---
# El explorador transmite una tupla (x, y, clase). Ignoramos cualquier otra cosa
# que aparezca en el canal (p.ej. broadcasts de otro programa/hub) y seguimos
# esperando, en vez de aceptar el primer dato y crashear.
objetivo = None
while objetivo is None:
    datos = radio.observe(config.CANAL)  # None si no oye nada hace ~1 s
    if isinstance(datos, (tuple, list)) and len(datos) == 3:
        objetivo = datos
    elif datos is not None:
        print("BLE ignorado (no es coordenada):", datos)
    wait(50)

tx, ty, clase = objetivo
print("Objetivo recibido: x=%d y=%d clase=%d" % (tx, ty, clase))
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

# Acercarse rapido hasta MARGEN_APROXIMACION antes de la coordenada; el ultimo
# tramo va DESPACIO y guiado por el sensor, para no embestir el objeto.
avance_ciego = dist - config.MARGEN_APROXIMACION
if avance_ciego < 0:
    avance_ciego = 0
robot.straight(avance_ciego)

# --- 3. Aproximacion final guiada por el ultrasonido ---
# Avanzar lento y frenar APENAS el objeto entra en rango de la garra
# (d <= DIST_AGARRE + TOLERANCIA_AGARRE). Si no aparece en CREEP_MAX, se rinde
# (no agarra) en vez de seguir de largo y llevarselo por delante.
en_rango = False
robot.drive(config.VEL_APROXIMACION, 0)
while robot.distance() < avance_ciego + config.CREEP_MAX:
    d = ultrasonido.distance()
    print("Ultrasonido: %d mm" % d)
    if d <= config.DIST_AGARRE + config.TOLERANCIA_AGARRE:
        en_rango = True
        break
    wait(20)
robot.stop()
avance_total = robot.distance()  # cuanto avanzo en total, para volver al origen

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
