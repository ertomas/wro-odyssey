# test-acercamiento.py
# ---------------------------------------------------------------------------
# MEDIR OFFSET_OBJETO (y verificar CY_CERCA) — EXPLORADOR, con el telefono
#
# Corre el acercamiento EXACTAMENTE como la mision (buscar, centrar, acercarse
# hasta CY_CERCA) y ahi SE QUEDA QUIETO, sin despejar ni transmitir. Ese es el
# punto donde la mision fija la coordenada del objeto, asi que es el unico lugar
# donde OFFSET_OBJETO se puede medir con sentido.
#
# POR QUE HACE FALTA ESTE PROGRAMA
#   En la mision, apenas frena calcula la coordenada y arranca el despeje
#   (retrocede, pivota, sale de costado). No hay tiempo de medir. Aca frena y
#   espera.
#
# OFFSET_OBJETO NO ES UNA PROPIEDAD DEL ROBOT
#   Es la distancia que queda entre el robot y el objeto EN EL MOMENTO en que el
#   acercamiento decide "llegue". Ese momento lo define CY_CERCA, asi que los dos
#   estan acoplados: si movés CY_CERCA, hay que volver a medir OFFSET_OBJETO.
#   Fija CY_CERCA PRIMERO (mirando el numero "altura Y" en el telefono) y recien
#   despues medi.
#
# COMO USARLO
#   1. Conecta el telefono al hub del explorador (pagina de deteccion) y
#      verifica que llegan datos.
#   2. Pone el objeto delante del robot, a la distancia tipica de la mision.
#   3. Corre. El robot busca, centra y se acerca. Cuando muestra "M" en la
#      pantalla y suena, FRENO en el punto de la coordenada.
#   4. MEDI CON REGLA: del MEDIO DEL EJE de las ruedas al centro del objeto, en
#      linea con el rumbo del robot. Ese numero es OFFSET_OBJETO.
#      (Medio del eje, NO el paragolpes: toda la odometria esta referida a ese
#       punto — ver docs/setup-cancha.md.)
#   5. Mientras espera sigue imprimiendo la camara, asi verificas de paso que el
#      cy final sea el CY_CERCA que esperabas.
#
# Repetilo 2-3 veces con el objeto a distintas distancias iniciales: si frena
# siempre a la misma distancia del objeto, el numero es confiable.
#
# Este archivo es autocontenido. Los valores tienen que quedar en SYNC con
# explorador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.messaging import AppData
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch
from umath import sin, cos, radians

# --- Parametros propios de esta prueba ---
AVANCE_INICIAL = 0     # mm en linea antes de buscar. La mision usa 650, pero para
                       # MEDIR da igual como llego: lo unico que importa es donde
                       # frena respecto del objeto. 0 para probar en poco espacio.
ESPERA_MEDIR = 60000   # ms que se queda quieto para que midas (1 minuto)

# --- Hardware y calibracion (SYNC con explorador/config.py) ---
WHEEL_DIAMETER = 56
AXLE_TRACK = 112

# --- Deteccion ---
CLASES_OBJETIVO = (0, 1)
CONFIANZA_MIN = 60
AREA_MIN_VALIDO = 2

# --- Centrado ---
CX_CENTRO = 50    # centro REAL de la imagen (antes 40; ver explorador/config.py)
CX_TOLERANCIA = 8
KP_CENTRADO = 1.5
CENTRADO_FINAL_TIMEOUT = 4000  # ms max girando en el lugar para centrar al final

# --- Acercamiento (lo que estamos calibrando) ---
OFFSET_OBJETO = 150    # mm adelante (SYNC con explorador/config.py)
CY_CERCA = 80
CY_PERDIDA_CERCA = 70
CONFIRMACIONES_CERCA = 3
AVANCE_MIN_ACERCAMIENTO = 200
PERDIDAS_MAX = 10
ACERCAMIENTO_MAX = 1500
ACERCAMIENTO_TIMEOUT = 25000

# --- Velocidades ---
VEL_BUSQUEDA = 15
VEL_ACERCAMIENTO = 120

hub = PrimeHub()
motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.A, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der,
                  wheel_diameter=WHEEL_DIAMETER, axle_track=AXLE_TRACK)

app = AppData([(0, 5)])  # 5 bytes del telefono en el modo 0

# --- Pose propia (igual que la mision) ---
x = 0.0
y = 0.0
robot.reset()
_d_prev = 0


def actualizar_pose():
    """Integra el avance reciente en (x, y). Devuelve el rumbo."""
    global x, y, _d_prev
    d = robot.distance()
    rumbo = robot.angle()
    paso = d - _d_prev
    x += paso * cos(radians(rumbo))
    y += paso * sin(radians(rumbo))
    _d_prev = d
    return rumbo


def leer_camara():
    clase, conf, cx, area, cy = app.get_bytes(mode=0)
    return clase, conf, cx, area, cy


def objeto_visible(clase, conf, area):
    return (clase in CLASES_OBJETIVO
            and conf >= CONFIANZA_MIN
            and area >= AREA_MIN_VALIDO)


# --- 1. Buscar ---
hub.display.char("B")
print("--- test-acercamiento ---")
print("CY_CERCA=%d  CX_CENTRO=%d" % (CY_CERCA, CX_CENTRO))
if AVANCE_INICIAL > 0:
    robot.straight(AVANCE_INICIAL)
robot.drive(0, VEL_BUSQUEDA)
while True:
    clase, conf, cx, area, cy = leer_camara()
    actualizar_pose()
    if objeto_visible(clase, conf, area):
        break
    wait(20)
robot.stop()

# --- 2. Centrar ---
hub.display.char("C")
while True:
    clase, conf, cx, area, cy = leer_camara()
    actualizar_pose()
    if objeto_visible(clase, conf, area):
        error = cx - CX_CENTRO
        if abs(error) <= 8:
            robot.stop()
            break
        robot.drive(0, error * KP_CENTRADO)
    else:
        robot.drive(0, VEL_BUSQUEDA)
    wait(20)

# --- 3. Acercarse (identico a la mision) ---
hub.display.char("A")
d_inicio = robot.distance()
confirmaciones = 0
perdidas = 0
cy_max = 0
motivo = "?"
reloj = StopWatch()
while True:
    clase, conf, cx, area, cy = leer_camara()
    actualizar_pose()
    avanzado = robot.distance() - d_inicio

    if avanzado >= ACERCAMIENTO_MAX or reloj.time() >= ACERCAMIENTO_TIMEOUT:
        robot.stop()
        motivo = "TOPE DE SEGURIDAD (CY_CERCA nunca se alcanzo)"
        break

    if objeto_visible(clase, conf, area):
        perdidas = 0
        if cy > cy_max:
            cy_max = cy
        if cy >= CY_CERCA and avanzado >= AVANCE_MIN_ACERCAMIENTO:
            confirmaciones += 1
            if confirmaciones >= CONFIRMACIONES_CERCA:
                robot.stop()
                motivo = "cy >= CY_CERCA confirmado"
                break
        else:
            confirmaciones = 0
        error = cx - CX_CENTRO
        robot.drive(VEL_ACERCAMIENTO, error * KP_CENTRADO)
    else:
        confirmaciones = 0
        perdidas += 1
        if perdidas == 1:
            robot.brake()
        if perdidas >= PERDIDAS_MAX:
            if cy_max >= CY_PERDIDA_CERCA:
                motivo = "perdido por el borde inferior (lo tenemos encima)"
                break
            robot.drive(0, VEL_BUSQUEDA)
    wait(20)

# --- 3b. Centrar ANTES de fijar la coordenada ---
# El paso 3 frena mirando SOLO cy, asi que el robot puede quedar apuntando al
# costado. Como la coordenada se proyecta en la direccion del RUMBO, eso la manda
# a otro punto. Giramos en el lugar hasta centrar.
cx_final = -1
reloj_centrado = StopWatch()
while reloj_centrado.time() < CENTRADO_FINAL_TIMEOUT:
    clase, conf, cx, area, cy = leer_camara()
    actualizar_pose()
    if not objeto_visible(clase, conf, area):
        break
    cx_final = cx
    error = cx - CX_CENTRO
    if abs(error) <= CX_TOLERANCIA:
        break
    robot.drive(0, error * KP_CENTRADO)
    wait(20)
robot.stop()

# --- 4. QUIETO: aca la mision fijaria la coordenada. Medir. ---
rumbo = actualizar_pose()
hub.display.char("M")  # "M" de Medir
hub.speaker.beep(frequency=880, duration=400)

print("")
print("FRENO. Motivo: %s" % motivo)
print("Pose: x=%d y=%d rumbo=%d | avanzado=%d mm | cy_max=%d"
      % (x, y, rumbo, robot.distance() - d_inicio, cy_max))
if cx_final < 0:
    print("cx final: objeto NO visible al centrar (se fue por el borde inferior)")
elif abs(cx_final - CX_CENTRO) <= CX_TOLERANCIA:
    print("cx final: %d  -> CENTRADO ok (objetivo %d +-%d)"
          % (cx_final, CX_CENTRO, CX_TOLERANCIA))
else:
    print("cx final: %d  -> NO centro (objetivo %d +-%d). Se agoto el timeout:"
          % (cx_final, CX_CENTRO, CX_TOLERANCIA))
    print("   la medicion lateral de esta corrida NO sirve.")
print("")
print(">>> MEDI AHORA, DOS DISTANCIAS:")
print(">>> (a) ADELANTE: del MEDIO DEL EJE al objeto, en linea con el rumbo.")
print(">>>     -> OFFSET_OBJETO")
print(">>> (b) AL COSTADO: cuanto queda el objeto corrido de la LINEA MEDIA")
print(">>>     del robot. derecha(+) / izquierda(-)  -> OFFSET_OBJETO_LATERAL")
print(">>>")
print(">>> (b) NO es cero: la camara no esta en la linea media, asi que al")
print(">>> centrar deja el objeto corrido. Medilo, no lo calcules.")
print("")
print("Coordenada transmitida segun lo que midas (adelante x lateral):")
for adelante in (OFFSET_OBJETO, OFFSET_OBJETO + 50):
    for costado in (-65, 0, 65):
        ox = int(x + adelante * cos(radians(rumbo)) - costado * sin(radians(rumbo)))
        oy = int(y + adelante * sin(radians(rumbo)) + costado * cos(radians(rumbo)))
        print("   adelante=%d lateral=%+d -> (%d, %d)" % (adelante, costado, ox, oy))
print("")
print("Camara en vivo (para verificar el cy final):")

reloj_espera = StopWatch()
while reloj_espera.time() < ESPERA_MEDIR:
    clase, conf, cx, area, cy = leer_camara()
    print("   clase=%d conf=%d cx=%d area=%d cy=%d" % (clase, conf, cx, area, cy))
    wait(1000)

hub.display.char("F")
print("--- fin ---")
