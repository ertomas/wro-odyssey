# test-aproximacion.py
# ---------------------------------------------------------------------------
# PRUEBA DE APROXIMACION Y AGARRE (sin navegacion, sin BLE, sin camara)
#
# Aisla el tramo mas delicado de la mision: acercarse al objeto y agarrarlo.
# No hay canal, no hay coordenada, no hay giro. Poner el objeto EN LINEA RECTA
# delante del robot y correr: el robot avanza, detecta, confirma, remata por
# odometria, agarra, levanta, vuelve al punto de partida y suelta.
#
# Es la misma secuencia que los pasos 3 y 4 de recuperador/main.py. Si esto
# anda, el unico riesgo que queda en la mision es la navegacion (que ya se
# valida con calibrar-ruedas.py) y la vision.
#
# POR QUE EN DOS TRAMOS
#   El ultrasonido solo es confiable de DIST_MIN_CONFIABLE para arriba; mas
#   cerca se clava en un valor de piso y salta. Asi que NO decide el agarre:
#   detecta lejos (donde ve bien) y el ultimo tramo lo hace la ODOMETRIA, que
#   sobre ~10 cm tiene error submilimetrico. Ver docs/calibracion.md.
#
# COMO USARLO
#   1. Pone el objeto REAL delante del robot, centrado y en linea recta, a una
#      distancia menor que BUSQUEDA_MAX.
#   2. Corre. Tenes PAUSA_INICIAL para sacar la mano.
#   3. Mira la terminal. Los numeros que importan:
#        "Detectado a N mm"            -> tiene que ser <= UMBRAL_DETECCION
#        "Confirmacion quieto: [...]"  -> las 5 lecturas tienen que estar JUNTAS.
#                                         Si vienen dispersas, subi UMBRAL_DETECCION.
#        "Avance final: N mm"          -> deberia dar ~ (mediana - DIST_OBJETIVO_FINAL)
#        "Garra cerrada en N deg"      -> comparalo con el valor de cerrar en VACIO
#                                         (corre esta prueba sin objeto una vez).
#                                         Si cierra igual que en vacio, no agarro nada.
#   4. El robot vuelve solo al punto de partida, asi que podes repetir moviendo
#      SOLO el objeto.
#
# Este archivo es autocontenido. Los valores tienen que quedar en SYNC con
# recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, UltrasonicSensor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# --- Parametros propios de esta prueba ---
PAUSA_INICIAL = 3000   # ms para acomodar el objeto y sacar la mano
BUSQUEDA_MAX = 800     # mm max que avanza buscando el objeto (aca no hay coordenada,
                       # asi que reemplaza a CREEP_MAX de la mision)
AVANCE_CIEGO = 0       # mm a ciegas antes de empezar a mirar el sensor. Dejalo en 0
                       # para probar solo la aproximacion; subilo si queres simular
                       # el tramo rapido de la mision (MARGEN_APROXIMACION).

# --- Hardware y calibracion (SYNC con recuperador/config.py) ---
WHEEL_DIAMETER = 56
AXLE_TRACK = 164

GARRA_VELOCIDAD = 300
GARRA_DUTY_LIMIT = 90
GARRA_DUTY_SOSTEN = 100

ELEVADOR_VELOCIDAD = 100
ELEVADOR_ANGULO_ARRIBA = -90

DIST_MIN_CONFIABLE = 54
UMBRAL_DETECCION = 150
DIST_OBJETIVO_FINAL = 45
ESPERA_ASENTAMIENTO = 400     # ms de marcha antes de creerle al sensor
CONFIRMACIONES_DETECCION = 3  # lecturas SEGUIDAS bajo el umbral
LECTURAS_CONFIRMACION = 5
MARGEN_CONFIRMACION = 50
VEL_APROXIMACION = 40

hub = PrimeHub()
motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.A, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der,
                  wheel_diameter=WHEEL_DIAMETER, axle_track=AXLE_TRACK)
# Suavizar la aceleracion: arrancar de golpe hace cabecear el chasis y el
# ultrasonido apunta al piso. SYNC con recuperador/config.py.
robot.settings(straight_acceleration=250, turn_acceleration=400)
garra = Motor(Port.C)
elevador = Motor(Port.D)
ultrasonido = UltrasonicSensor(Port.E)

hub.display.char("P")  # "P" de Prueba (antes de mover motores)
print("--- test-aproximacion ---")
print("umbral=%d  objetivo_final=%d  min_confiable=%d"
      % (UMBRAL_DETECCION, DIST_OBJETIVO_FINAL, DIST_MIN_CONFIABLE))

# --- Arrancar "abierta y abajo" (igual que la mision) ---
elevador.reset_angle(0)
garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)  # abrir
# SOSTENER la apertura: run_until_stalled termina en COAST, y sin fuerza la garra
# deriva hacia adentro con el tiron del arranque. CERRADA se mete en el cono del
# ultrasonido (~89 mm) y dispara un falso positivo al instante.
garra.hold()

d0 = ultrasonido.distance()
print("Lectura inicial: %d mm" % d0)
if d0 <= UMBRAL_DETECCION:
    print("OJO: lee cerca ANTES de arrancar. Revisar que la garra este abierta")
    print("     y fuera del cono, y que no haya nada delante.")

wait(PAUSA_INICIAL)
robot.reset()

# --- Tramo a ciegas (opcional) ---
if AVANCE_CIEGO > 0:
    robot.straight(AVANCE_CIEGO)

# --- 1 y 2. Detectar y confirmar, con REINTENTO ---
# Una deteccion que no se sostiene con el robot quieto no aborta la prueba: se
# vuelve a arrancar y se sigue buscando. El caso tipico es el cabeceo del
# arranque, que dura un instante y desaparece al frenar.
limite = AVANCE_CIEGO + BUSQUEDA_MAX
confirmado = False
d_confirmado = 0
descartes = 0

while robot.distance() < limite and not confirmado:
    detectado = False
    d_deteccion = 0
    robot.drive(VEL_APROXIMACION, 0)
    wait(ESPERA_ASENTAMIENTO)  # ignorar el cabeceo del arranque
    seguidas = 0
    while robot.distance() < limite:
        d = ultrasonido.distance()
        if d <= UMBRAL_DETECCION:
            seguidas += 1
            if seguidas >= CONFIRMACIONES_DETECCION:
                detectado = True
                d_deteccion = d
                break
        else:
            seguidas = 0  # se corto la racha: era un pico
        wait(20)
    robot.stop()

    if not detectado:
        break

    print("Detectado a %d mm (tras avanzar %d mm)" % (d_deteccion, robot.distance()))

    # Confirmar QUIETO: saca el ruido de la marcha, deja asentar el cabeceo y
    # mide desde donde el robot QUEDO (absorbe el sobrepaso del frenado).
    lecturas = []
    for _ in range(LECTURAS_CONFIRMACION):
        lecturas.append(ultrasonido.distance())
        wait(30)
    lecturas.sort()
    d_confirmado = lecturas[len(lecturas) // 2]
    print("Confirmacion quieto: %s -> mediana %d mm" % (lecturas, d_confirmado))
    print("Dispersion: %d mm (si es grande, subi UMBRAL_DETECCION)"
          % (lecturas[-1] - lecturas[0]))

    if d_confirmado <= UMBRAL_DETECCION + MARGEN_CONFIRMACION:
        confirmado = True
    else:
        descartes += 1
        print("DESCARTADO #%d: quieto lee %d mm. Era cabeceo o ruido. Sigo."
              % (descartes, d_confirmado))

if descartes:
    print("(hubo %d deteccion(es) falsa(s); si son muchas, bajá ACELERACION o"
          " subí ESPERA_ASENTAMIENTO)" % descartes)

if not confirmado:
    print("NO DETECTADO en %d mm. El objeto estaba fuera de alcance," % BUSQUEDA_MAX)
    print("o el sensor no lo ve (probalo con calibrar-ultrasonido.py).")
    hub.display.char("X")
    hub.speaker.beep(frequency=220, duration=600)
    robot.straight(-robot.distance())
    raise SystemExit

avance_final = d_confirmado - DIST_OBJETIVO_FINAL
print("Avance final: %d mm" % avance_final)
if avance_final > 0:
    robot.straight(avance_final)
else:
    print("(ya estaba mas cerca que el objetivo: no avanzo)")

avance_total = robot.distance()
print("Avance total: %d mm" % avance_total)
print("VERIFICA CON REGLA: el objeto deberia estar en la garra ahora.")

# --- 3. Agarrar: ABRIR -> BAJAR -> CERRAR -> SOSTENER -> SUBIR ---
hub.display.char("G")
garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)   # abrir
garra.hold()                                                            # sostener la apertura
elevador.run_target(ELEVADOR_VELOCIDAD, 0)                              # asegurar abajo
garra.run_until_stalled(-GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)  # cerrar

# El angulo de cierre delata si agarro algo: con objeto frena ANTES que en vacio.
# Corre esta prueba una vez SIN objeto para conocer el valor de "cerrada vacia".
print("Garra cerrada en %d deg (comparar con el cierre en VACIO)" % garra.angle())

garra.dc(-GARRA_DUTY_SOSTEN)  # sostener: run_until_stalled deja coast y se cae
elevador.run_target(ELEVADOR_VELOCIDAD, ELEVADOR_ANGULO_ARRIBA)  # subir
hub.speaker.beep(frequency=880, duration=400)
print("Levantado. Mira si el objeto quedo bien tomado.")
wait(2000)

# --- 4. Volver al punto de partida y soltar ---
# Asi podes repetir la prueba moviendo SOLO el objeto.
robot.straight(-avance_total)
hub.display.char("A")
elevador.run_target(ELEVADOR_VELOCIDAD, 0)                             # bajar
garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)  # soltar

hub.display.char("F")
print("--- fin ---")
