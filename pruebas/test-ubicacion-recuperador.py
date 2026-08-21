# test-ubicacion-recuperador.py
# ---------------------------------------------------------------------------
# PRUEBA DE UBICACION (2 de 2)
#
# Escucha el canal BLE. Cuando el explorador (test-ubicacion-explorador.py, en
# el otro hub) transmite el sitio (x, y, clase), navega hasta ahi con su propia
# odometria, hace la APROXIMACION FINAL despacio guiada por el ultrasonido
# (frena apenas el objeto entra en rango, sin embestirlo), BAJA la garra, la
# CIERRA para agarrar, vuelve a su origen y suelta. Sirve para confirmar
# odometria + navegacion + ultrasonido + garra juntas, SIN CAMARA.
#
# Es la MISMA secuencia que recuperador/main.py, solo que la coordenada la manda
# el test del explorador en vez de la camara. Si esto anda, lo unico que queda
# por depurar en la mision es la vision.
#
# HARDWARE DE LA GARRA:
#   - Port.C: motor que ABRE/CIERRA la pinza (run_until_stalled). En ESTE robot
#     abre con velocidad + y cierra con velocidad - (al reves de lo tipico).
#     Tras cerrar se mantiene el apriete con dc() (si no, coast = suelta la fuerza).
#   - Port.D: motor ELEVADOR que SUBE/BAJA la garra. No tiene tope arriba, pero
#     en reposo queda ABAJO: esa posicion (donde queda al arrancar) es el cero.
#     Subir = run_target(ELEVADOR_ANGULO_ARRIBA); bajar = run_target(0).
#   - Port.E: sensor de ULTRASONIDO, montado a ~7 cm del punto de agarre.
#
# La garra ARRANCA abierta y ABAJO; al llegar al punto cierra y recien ahi SUBE;
# al terminar el ciclo vuelve a quedar ABAJO (posicion inicial de reposo).
#
# POSICION DE ARRANQUE: el recuperador NO arranca en el mismo punto que el
# explorador. Arranca 165 mm a la IZQUIERDA, mirando en la MISMA direccion
# (+x adelante). Para navegar en SU propio marco le restamos ese offset.
#
# SIGNO DE +Y (verificado 2026-08-20): turn() positivo gira a la DERECHA
# (horario), la convencion estandar de Pybricks. El explorador integra su pose
# con y += paso*sin(rumbo) usando ese mismo rumbo, asi que en el marco compartido
# +y es la DERECHA fisica. Izquierda = -y, por eso OFFSET_Y es NEGATIVO.
#
# Usa BLERadio (pybricks.messaging), la MISMA API que recuperador/main.py.
# Este archivo es autocontenido (no importa config.py). Los valores de abajo
# tienen que quedar en SYNC con recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, UltrasonicSensor
from pybricks.messaging import BLERadio
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait
from umath import atan2, degrees, sqrt

# --- Parametros de la prueba (SYNC con recuperador/config.py) ---
CANAL = 1                 # el mismo que transmite el explorador
GARRA_VELOCIDAD = 300     # deg/s al abrir/cerrar la pinza
GARRA_DUTY_LIMIT = 90     # % de fuerza al cerrar/abrir
GARRA_DUTY_SOSTEN = 100   # % de fuerza CONTINUA para mantener el objeto agarrado
                          # (run_until_stalled suelta al terminar; con dc() sigue
                          #  apretando mientras carga el objeto)

# Elevador (Port.D): en reposo queda ABAJO; esa posicion al arrancar es el cero.
ELEVADOR_VELOCIDAD = 100      # deg/s
ELEVADOR_ANGULO_ARRIBA = -90  # deg desde "abajo" (cero) hasta "levantada"
                              # (CALIBRAR: si baja en vez de subir, invertir el signo)

# Ultrasonido + aproximacion final (Port.E). MEDIDO 2026-08-20: el sensor solo
# es confiable de 54 mm para arriba (mas cerca se clava en 40 y salta), y la
# garra agarra hasta 55. Se solapan en 1 mm, asi que el sensor NO puede decidir
# "el objeto esta en la garra". La aproximacion va en DOS TRAMOS: detectar a
# UMBRAL_DETECCION (zona confiable), frenar, re-medir quieto y cubrir el resto
# con ODOMETRIA. Ver recuperador/config.py.
DIST_MIN_CONFIABLE = 54     # mm: por debajo de esto la lectura no sirve (referencia)
UMBRAL_DETECCION = 150      # mm: lectura a la que se da por detectado el objeto
DIST_OBJETIVO_FINAL = 45    # mm: donde queremos dejar el objeto antes de cerrar
ESPERA_ASENTAMIENTO = 400   # ms de marcha antes de creerle al sensor (el tiron del
                            # arranque hace saltar la lectura y disparaba el agarre)
CONFIRMACIONES_DETECCION = 3  # lecturas SEGUIDAS bajo el umbral para dar por detectado
LECTURAS_CONFIRMACION = 5   # lecturas quietas antes del tramo final (se usa la MEDIANA)
MARGEN_CONFIRMACION = 50    # mm: si quieto lee mas de UMBRAL+esto, era ruido -> se rinde
MARGEN_APROXIMACION = 300   # mm antes de la coordenada donde deja de manejar a ciegas
VEL_APROXIMACION = 40       # mm/s del tramo de busqueda
CREEP_MAX = 550             # mm max de avance lento buscando el objeto

# Posicion del recuperador en el marco del explorador (+y = DERECHA fisica).
OFFSET_X = 0              # mm: mismo "adelante" que el explorador
OFFSET_Y = -165           # mm: 165 a la IZQUIERDA del explorador -> negativo

# --- Hardware calibrado (SYNC con recuperador/config.py) ---
hub = PrimeHub()
radio = BLERadio(observe_channels=[CANAL])
motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.A, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=164)
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
# SOSTENER la apertura: run_until_stalled termina en COAST y la garra deriva con
# el tiron del arranque. CERRADA se mete en el cono del sensor (~89 mm) -> falso
# positivo. Medido con diag-ultrasonido.py el 2026-08-20.
garra.hold()

# --- 1. Esperar una coordenada VALIDA del explorador ---
# Ignoramos cualquier otra cosa que aparezca en el canal (p.ej. broadcasts de
# otro programa/hub) y seguimos esperando, en vez de aceptar el primer dato y
# crashear al desempaquetarlo.
objetivo = None
while objetivo is None:
    datos = radio.observe(CANAL)  # None si no oye nada hace ~1 s
    if isinstance(datos, (tuple, list)) and len(datos) == 3:
        objetivo = datos
    elif datos is not None:
        print("BLE ignorado (no es coordenada):", datos)
    wait(50)

tx, ty, clase = objetivo
print("Objetivo recibido: x=%d y=%d clase=%d" % (tx, ty, clase))
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

# Acercarse rapido hasta MARGEN_APROXIMACION antes de la coordenada; el ultimo
# tramo va DESPACIO y guiado por el sensor, para no embestir el objeto.
avance_ciego = dist - MARGEN_APROXIMACION
if avance_ciego < 0:
    avance_ciego = 0
print("Rumbo %d deg | dist %d mm | avance a ciegas %d mm"
      % (rumbo, dist, avance_ciego))
robot.straight(avance_ciego)

# --- 3. Aproximacion final en DOS TRAMOS ---
# 3a. Buscar: avanzar despacio hasta detectar el objeto a UMBRAL_DETECCION (zona
#     confiable del sensor). Si no aparece en CREEP_MAX, se rinde.
en_rango = False
robot.drive(VEL_APROXIMACION, 0)
wait(ESPERA_ASENTAMIENTO)  # ignorar el tiron del arranque
seguidas = 0
while robot.distance() < avance_ciego + CREEP_MAX:
    d = ultrasonido.distance()
    print("Ultrasonido: %d mm" % d)
    if d <= UMBRAL_DETECCION:
        seguidas += 1
        if seguidas >= CONFIRMACIONES_DETECCION:
            en_rango = True
            break
    else:
        seguidas = 0  # se corto la racha: era un pico
    wait(20)
robot.stop()

# 3b. Confirmar QUIETO (mediana) y cubrir el resto con odometria. Medir parado
#     absorbe el sobrepaso del frenado: el avance sale de la posicion REAL.
if en_rango:
    lecturas = []
    for _ in range(LECTURAS_CONFIRMACION):
        lecturas.append(ultrasonido.distance())
        wait(30)
    lecturas.sort()
    d_confirmado = lecturas[len(lecturas) // 2]
    print("Confirmacion quieto: %s -> mediana %d mm" % (lecturas, d_confirmado))

    if d_confirmado > UMBRAL_DETECCION + MARGEN_CONFIRMACION:
        print("Descartado: quieto lee %d mm, era ruido" % d_confirmado)
        en_rango = False
    else:
        avance_final = d_confirmado - DIST_OBJETIVO_FINAL
        print("Avance final por odometria: %d mm" % avance_final)
        if avance_final > 0:
            robot.straight(avance_final)

avance_total = robot.distance()  # cuanto avanzo en total, para volver al origen
print("Fin de la aproximacion: avance_total=%d mm | en_rango=%s" % (avance_total, en_rango))

# --- 4. Agarrar solo si confirmamos el objeto en rango ---
# Secuencia: ABRIR -> BAJAR -> CERRAR -> SOSTENER -> SUBIR. Se abre ANTES de bajar
# para que la garra descienda abierta y rodee el objeto en vez de golpearlo.
if en_rango:
    hub.display.char("G")  # "G" de Garra
    garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)   # abrir
    garra.hold()  # sostener la apertura mientras se mueve el elevador
    elevador.run_target(ELEVADOR_VELOCIDAD, 0)  # asegurar abajo (ya abierta, no golpea)
    garra.run_until_stalled(-GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)  # cerrar
    garra.dc(-GARRA_DUTY_SOSTEN)  # seguir apretando para no soltar el objeto al moverse
    elevador.run_target(ELEVADOR_VELOCIDAD, ELEVADOR_ANGULO_ARRIBA)  # subir con el objeto
    hub.speaker.beep(frequency=880, duration=400)
else:
    # No se pudo confirmar objeto al alcance: avisar y no cerrar la garra.
    hub.display.char("X")
    hub.speaker.beep(frequency=220, duration=600)

# --- 5. Volver a su origen (compensando todo lo que avanzo en el paso 3) ---
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
