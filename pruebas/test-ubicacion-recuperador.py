# test-ubicacion-recuperador.py
# ---------------------------------------------------------------------------
# PRUEBA DE UBICACION (2 de 2)
#
# Escucha el canal BLE. Cuando el explorador (test-ubicacion-explorador.py, en
# el otro hub) transmite el sitio (x, y, clase), navega hasta ahi con su propia
# odometria, CONFIRMA con el ultrasonido que el objeto esta al alcance de la
# garra (y corrige el avance final si hace falta), BAJA la garra, la CIERRA para
# agarrar, vuelve a su origen y suelta. Sirve para confirmar odometria +
# navegacion + ultrasonido + garra juntas, sin camara.
#
# HARDWARE DE LA GARRA:
#   - Port.C: motor que ABRE/CIERRA la pinza (run_until_stalled). En ESTE robot
#     abre con velocidad + y cierra con velocidad - (al reves de lo tipico).
#     Tras cerrar se mantiene el apriete con dc() (si no, coast = suelta la fuerza).
#   - Port.D: motor ELEVADOR que SUBE/BAJA la garra. No tiene tope arriba, pero
#     en reposo queda ABAJO: esa posicion (donde queda al arrancar) es el cero.
#     Subir = run_target(ELEVADOR_ANGULO_ARRIBA); bajar = run_target(0).
#   - Port.E: sensor de ULTRASONIDO, montado a 7 cm (70 mm) del punto de agarre.
#     Un objeto justo en la garra se lee en ~70 mm.
#
# La garra ARRANCA abierta y ABAJO; al llegar al punto cierra y recien ahi SUBE;
# al terminar el ciclo vuelve a quedar ABAJO (posicion inicial de reposo).
#
# POSICION DE ARRANQUE: el recuperador NO arranca en el mismo punto que el
# explorador. Arranca 200 mm a la IZQUIERDA del explorador, mirando en la MISMA
# direccion (+x adelante). En ESTOS robots (verificado en cancha) turn() positivo
# gira a la IZQUIERDA, asi que en el marco compartido +y apunta a la IZQUIERDA:
# "izquierda" es +y y el recuperador esta en (0, +200) de ese marco. Para navegar
# en SU propio marco le restamos ese offset al objetivo (ver OFFSET_X / OFFSET_Y).
#
# Este archivo es autocontenido (no importa config.py). Los valores de hardware
# de abajo tienen que quedar en SYNC con recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, UltrasonicSensor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait
from umath import atan2, degrees, sqrt

# --- Parametros de la prueba ---
CANAL = 1                 # el mismo que transmite el explorador
GARRA_VELOCIDAD = 300     # deg/s al abrir/cerrar la pinza
GARRA_DUTY_LIMIT = 90     # % de fuerza al cerrar/abrir
GARRA_DUTY_SOSTEN = 100   # % de fuerza CONTINUA para mantener el objeto agarrado
                          # (run_until_stalled suelta al terminar; con dc() sigue
                          #  apretando mientras carga el objeto)

# Elevador (Port.D): en reposo queda ABAJO; esa posicion al arrancar es el cero.
# Se sube/baja por angulo fijo (run_target sobre ese cero).
ELEVADOR_VELOCIDAD = 100      # deg/s
ELEVADOR_ANGULO_ARRIBA = -90  # deg desde "abajo" (cero) hasta "levantada"
                              # (CALIBRAR: si baja en vez de subir, invertir el signo)

# Ultrasonido (Port.E): el sensor esta a 7 cm (70 mm) del punto de agarre, asi
# que un objeto justo en la garra se lee en ~70 mm.
DIST_AGARRE = 60          # mm: lectura esperada con el objeto en la garra
TOLERANCIA = 15           # mm: dentro de esto se considera "en rango"
DIST_SIN_OBJETO = 250     # mm: mas alla de esto se asume que no hay objeto
PASO_MAX = 20             # mm: correccion maxima de avance por intento
INTENTOS_MAX = 5          # cuantas veces reintenta acercarse antes de rendirse

# Posicion del recuperador en el marco del explorador (izquierda = +y en estos
# robots, verificado en cancha).
OFFSET_X = 0              # mm: mismo "adelante" que el explorador
OFFSET_Y = 200           # mm: 20 cm a la izquierda del explorador

# --- Hardware calibrado (mantener en sync con recuperador/config.py) ---
hub = PrimeHub(observe_channels=[CANAL])
motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.A, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=160)
garra = Motor(Port.C)               # abre/cierra la pinza
elevador = Motor(Port.D)            # sube/baja la garra
ultrasonido = UltrasonicSensor(Port.E)

hub.display.char("R")  # "R" de Recuperador (se muestra ANTES de mover motores,
                       # asi si se traba sabemos que fue en un movimiento y no en
                       # la deteccion de los dispositivos)

# --- Arrancar "abierta y abajo" ---
# El elevador arranca en reposo (abajo): fijamos ese punto como cero y solo
# abrimos la garra. Se MANTIENE ABAJO; recien sube DESPUES de agarrar el objeto.
elevador.reset_angle(0)
garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)   # abrir

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

# --- 3. Confirmar con el ultrasonido y corregir el avance final ---
# El objeto deberia leerse en ~DIST_AGARRE (70 mm). Si esta un poco lejos/cerca,
# avanzamos/retrocedemos en pasos chicos hasta entrar en rango. Vamos acumulando
# el avance real en avance_total para poder volver exacto al origen despues.
avance_total = dist
en_rango = False
for intento in range(INTENTOS_MAX):
    d = ultrasonido.distance()
    print("Ultrasonido %d: %d mm" % (intento, d))
    if d > DIST_SIN_OBJETO:            # no ve nada -> reintentar (puede ser ruido)
        wait(100)
        continue
    error = d - DIST_AGARRE            # >0 objeto lejos, <0 objeto muy cerca
    if abs(error) <= TOLERANCIA:
        en_rango = True
        break
    # Corregir avanzando (+) o retrocediendo (-), sin pasarse de PASO_MAX.
    paso = PASO_MAX if error > PASO_MAX else (-PASO_MAX if error < -PASO_MAX else error)
    robot.straight(paso)
    avance_total += paso
    wait(100)                          # dejar asentar la proxima lectura

# --- 4. Agarrar solo si confirmamos el objeto en rango ---
# Secuencia: ABRIR -> BAJAR -> CERRAR -> SUBIR. Se abre ANTES de bajar para que
# la garra descienda abierta y rodee el objeto en vez de golpearlo.
if en_rango:
    hub.display.char("G")  # "G" de Garra
    garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)   # abrir
    elevador.run_target(ELEVADOR_VELOCIDAD, 0)  # bajar (ya abierta, no golpea)
    garra.run_until_stalled(-GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)  # cerrar
    garra.dc(-GARRA_DUTY_SOSTEN)  # seguir apretando para no soltar el objeto al moverse
    elevador.run_target(ELEVADOR_VELOCIDAD, ELEVADOR_ANGULO_ARRIBA)  # subir con el objeto
    hub.speaker.beep(frequency=880, duration=400)
else:
    # No se pudo confirmar objeto al alcance: avisar y no cerrar la garra.
    hub.display.char("X")
    hub.speaker.beep(frequency=220, duration=600)

# --- 5. Volver a su origen (compensando las correcciones del paso 3) ---
robot.straight(-avance_total)
robot.turn(-rumbo)

# --- 6. Soltar el objeto (si lo agarramos) y dejar la garra en la posicion
#        inicial: elevador ABAJO (cero de reposo). ---
if en_rango:
    hub.display.char("A")  # "A" de Abrir
    elevador.run_target(ELEVADOR_VELOCIDAD, 0)  # bajar
    garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)  # abrir/soltar
else:
    elevador.run_target(ELEVADOR_VELOCIDAD, 0)  # bajar a la posicion inicial

hub.display.char("F")  # "F" de Fin
