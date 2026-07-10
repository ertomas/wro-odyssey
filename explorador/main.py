# main.py  (EXPLORADOR)
# ---------------------------------------------------------------------------
# ROBOT EXPLORADOR
#
# Usa el telefono como camara (pagina /deteccion-objeto con Teachable Machine).
# El telefono manda 4 bytes por AppData:  [clase, confianza, cx, area]
#   clase     -> indice de categoria del modelo (0 = primera clase)
#   confianza -> 0..100 (% de certeza)
#   cx        -> 0..100 (centro horizontal del objeto; 50 = centrado)
#   area      -> 0..100 (tamano relativo del objeto = proxi de distancia)
#
# El explorador: (1) busca girando, (2) acentra el objeto con la camara,
# (3) se acerca, (4) calcula la posicion (x, y) con su propia odometria y la
# TRANSMITE por BLE al recuperador.
#
# Origen acordado: ambos robots arrancan en (0, 0) mirando hacia +x (0 grados).
# Todos los parametros ajustables estan en config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.messaging import AppData
from pybricks.tools import wait
from umath import sin, cos, radians

import config

# El canal tiene que ser el mismo que escucha el recuperador.
hub = PrimeHub(broadcast_channel=config.CANAL)

motor_izq = Motor(config.PUERTO_MOTOR_IZQ, config.DIRECCION_MOTOR_IZQ)
motor_der = Motor(config.PUERTO_MOTOR_DER, config.DIRECCION_MOTOR_DER)
robot = DriveBase(
    motor_izq, motor_der,
    wheel_diameter=config.WHEEL_DIAMETER,
    axle_track=config.AXLE_TRACK,
)

# Buffer de la camara del telefono: 4 bytes en el modo 0.
app = AppData([(0, 4)])

# --- Pose propia: x, y en mm; el rumbo lo da robot.angle() en grados ---
x = 0.0
y = 0.0
robot.reset()
_d_prev = 0


def actualizar_pose():
    """Integra el avance reciente en la posicion (x, y). Devuelve el rumbo."""
    global x, y, _d_prev
    d = robot.distance()
    rumbo = robot.angle()
    paso = d - _d_prev
    x += paso * cos(radians(rumbo))
    y += paso * sin(radians(rumbo))
    _d_prev = d
    return rumbo


def leer_camara():
    """Devuelve (clase, confianza, cx, area) que manda el telefono."""
    clase, conf, cx, area = app.get_bytes(mode=0)
    return clase, conf, cx, area


# --- 1. Buscar el objeto: primero avanzar, despues girar en el lugar ---
hub.display.char("B")
clase_detectada = config.CLASES_OBJETIVO[0]  # cual de las clases objetivo vimos
robot.straight(config.AVANCE_INICIAL)  # avanzar en linea antes de empezar a buscar
robot.drive(0, config.VEL_BUSQUEDA)  # girar en el lugar
while True:
    clase, conf, cx, area = leer_camara()
    actualizar_pose()
    if clase in config.CLASES_OBJETIVO and conf >= config.CONFIANZA_MIN:
        clase_detectada = clase
        break
    wait(20)
robot.stop()

# --- 2. Centrar el objeto en la camara (centrado visual) ---
hub.display.char("C")
while True:
    clase, conf, cx, area = leer_camara()
    actualizar_pose()
    if clase in config.CLASES_OBJETIVO and conf >= config.CONFIANZA_MIN:
        clase_detectada = clase
        error = cx - config.CX_CENTRO  # >0 = objeto a la derecha
        if abs(error) <= config.CX_TOLERANCIA:
            robot.stop()
            break
        robot.drive(0, error * config.KP_CENTRADO)  # girar proporcional al error
    else:
        robot.drive(0, config.VEL_BUSQUEDA)  # se perdio: seguir buscando
    wait(20)

# --- 3. Acercarse hasta tener el objeto bien grande (cerca) ---
hub.display.char("A")
while True:
    clase, conf, cx, area = leer_camara()
    actualizar_pose()
    if area >= config.AREA_CERCA:
        robot.stop()
        break
    error = cx - config.CX_CENTRO
    robot.drive(config.VEL_ACERCAMIENTO, error * config.KP_CENTRADO)
    wait(20)

# --- 4. Fijar la posicion del objeto (todavia cerca, ANTES de retroceder) ---
# Importante: calcular aca, con la pose en el punto de acercamiento. Si se calcula
# despues del retroceso, la coordenada queda corrida hacia atras.
rumbo = actualizar_pose()
# El objeto esta justo delante; sumamos un offset en la direccion del rumbo.
obj_x = int(x + config.OFFSET_OBJETO * cos(radians(rumbo)))
obj_y = int(y + config.OFFSET_OBJETO * sin(radians(rumbo)))

# --- 5. Liberar la zona: retroceder para no tapar el objeto al recuperador ---
robot.straight(-config.RETROCESO_FINAL)

# --- 6. Transmitir la coordenada del objeto ---
hub.display.char("T")
hub.speaker.beep()

# Transmitir varias veces (~5 s) para asegurar que el recuperador lo reciba.
for _ in range(50):
    hub.ble.broadcast((obj_x, obj_y, clase_detectada))
    wait(100)

hub.display.char("F")
