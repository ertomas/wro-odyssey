# main.py  (EXPLORADOR)
# ---------------------------------------------------------------------------
# ROBOT EXPLORADOR
#
# Usa el telefono como camara (pagina /deteccion-objeto con Teachable Machine).
# El telefono manda 5 bytes por AppData:  [clase, confianza, cx, area, cy]
#   clase     -> indice de categoria del modelo (0 = primera clase)
#   confianza -> 0..100 (% de certeza)
#   cx        -> 0..100 (centro horizontal del objeto; 50 = centrado)
#   area      -> 0..100 (tamano relativo del objeto)
#   cy        -> 0..100 (altura del borde INFERIOR del objeto en el cuadro:
#                0 = arriba/lejos, 100 = abajo del todo/encima)
#
# EL TELEFONO VA INCLINADO HACIA ABAJO, no mirando al horizonte. Vertical, el
# objeto se escapa por el borde inferior del cuadro justo cuando el robot esta
# mas cerca (que es donde hay que fijar la coordenada) y el robot lo embiste.
# Inclinado, el objeto sigue a la vista y ademas cy se vuelve un indicador de
# distancia confiable: el objeto apoyado en el piso baja en el cuadro de forma
# monotona al acercarse, sin depender de la luz ni del fondo (a diferencia del area).
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
from pybricks.messaging import AppData, BLERadio
from pybricks.tools import wait, StopWatch
from umath import sin, cos, radians

import config

hub = PrimeHub()
# Mensajeria BLE (firmware nuevo): transmitir por el canal que escucha el
# recuperador. El canal tiene que ser el MISMO en los dos robots.
radio = BLERadio(broadcast_channel=config.CANAL)

motor_izq = Motor(config.PUERTO_MOTOR_IZQ, config.DIRECCION_MOTOR_IZQ)
motor_der = Motor(config.PUERTO_MOTOR_DER, config.DIRECCION_MOTOR_DER)
robot = DriveBase(
    motor_izq, motor_der,
    wheel_diameter=config.WHEEL_DIAMETER,
    axle_track=config.AXLE_TRACK,
)
# Suavizar la aceleracion. La odometria de este robot produce la coordenada que
# consume el resto de la mision, y el patinaje por arrancar/frenar de golpe es un
# error que los encoders NO ven. Ir suave cuesta unos segundos y compra precision.
robot.settings(
    straight_acceleration=config.ACELERACION_RECTA,
    turn_acceleration=config.ACELERACION_GIRO,
)

# Buffer de la camara del telefono: 5 bytes en el modo 0.
app = AppData([(0, 5)])

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


def giro_centrado(error):
    """Velocidad de giro proporcional al error de cx, CON TOPE.

    Sin tope, un error grande (cx puede estar a +-50 del centro) por
    KP_CENTRADO pide un giro muy rapido de golpe: el robot pega un tiron, las
    ruedas patinan y la odometria se ensucia. Y el patinaje es justo lo que los
    encoders NO ven, asi que el error entra en la coordenada transmitida sin
    dejar rastro. Con tope es el mismo control, pero sin sacudones.
    """
    rate = error * config.KP_CENTRADO
    if rate > config.VEL_GIRO_MAX:
        return config.VEL_GIRO_MAX
    if rate < -config.VEL_GIRO_MAX:
        return -config.VEL_GIRO_MAX
    return rate


def leer_camara():
    """Devuelve (clase, confianza, cx, area, cy) que manda el telefono."""
    clase, conf, cx, area, cy = app.get_bytes(mode=0)
    return clase, conf, cx, area, cy


def objeto_visible(clase, conf, area):
    """True si le creemos al blob: clase objetivo, confianza alta y area no ruido.

    El area minima importa porque clase/confianza salen de Teachable Machine y
    cx/cy salen del blob de color: son independientes. Sin este filtro, el modelo
    puede decir "egipto" mientras el blob no ve nada, y la pagina manda un cx
    cualquiera que se traduce en un giro fantasma.
    """
    return (clase in config.CLASES_OBJETIVO
            and conf >= config.CONFIANZA_MIN
            and area >= config.AREA_MIN_VALIDO)


# --- 1. Buscar el objeto: primero avanzar, despues girar en el lugar ---
hub.display.char("B")
clase_detectada = config.CLASES_OBJETIVO[0]  # cual de las clases objetivo vimos
robot.straight(config.AVANCE_INICIAL)  # avanzar en linea antes de empezar a buscar
robot.drive(0, config.VEL_BUSQUEDA)  # girar en el lugar
while True:
    clase, conf, cx, area, cy = leer_camara()
    actualizar_pose()
    if objeto_visible(clase, conf, area):
        clase_detectada = clase
        break
    wait(20)
robot.stop()

# --- 2. Centrar el objeto en la camara (centrado visual) ---
hub.display.char("C")
while True:
    clase, conf, cx, area, cy = leer_camara()
    actualizar_pose()
    if objeto_visible(clase, conf, area):
        clase_detectada = clase
        error = cx - config.CX_CENTRO  # >0 = objeto a la derecha
        if abs(error) <= config.CX_TOLERANCIA:
            robot.stop()
            break
        robot.drive(0, giro_centrado(error))  # girar proporcional al error, con tope
    else:
        robot.drive(0, config.VEL_BUSQUEDA)  # se perdio: seguir buscando
    wait(20)

# --- 3. Acercarse hasta tener el objeto abajo del cuadro (cerca) ---
# El criterio de "ya llegue" es cy (que tan abajo esta el objeto en el cuadro), no
# el area: con la camara inclinada cy baja de forma monotona al acercarse y no lo
# afecta la luz ni el fondo del mismo tono. Ademas hay que haber avanzado de verdad,
# porque si no una lectura alta suelta fijaria la coordenada desde lejos, donde el
# OFFSET_OBJETO fijo de 150 mm no representa nada.
hub.display.char("A")
d_inicio = robot.distance()
confirmaciones = 0
perdidas = 0
cy_max = 0          # el cy mas alto que llegamos a ver: dice si estuvimos cerca
reloj = StopWatch()
while True:
    clase, conf, cx, area, cy = leer_camara()
    actualizar_pose()
    avanzado = robot.distance() - d_inicio

    # Topes de seguridad: nunca quedarse colgado en este paso.
    if avanzado >= config.ACERCAMIENTO_MAX or reloj.time() >= config.ACERCAMIENTO_TIMEOUT:
        robot.stop()
        break

    if objeto_visible(clase, conf, area):
        clase_detectada = clase
        perdidas = 0
        if cy > cy_max:
            cy_max = cy
        if cy >= config.CY_CERCA and avanzado >= config.AVANCE_MIN_ACERCAMIENTO:
            confirmaciones += 1
            if confirmaciones >= config.CONFIRMACIONES_CERCA:
                robot.stop()
                break
        else:
            confirmaciones = 0
        error = cx - config.CX_CENTRO
        robot.drive(config.VEL_ACERCAMIENTO, giro_centrado(error))
    else:
        # Objeto perdido: FRENAR. Antes seguia avanzando a ciegas y por eso a veces
        # colisionaba: perder el objeto es justamente lo que pasa cuando lo tenes
        # encima y se sale por el borde inferior del cuadro.
        confirmaciones = 0
        perdidas += 1
        if perdidas == 1:
            robot.brake()   # brake() y no stop(): stop() es coast y sigue rodando
        if perdidas >= config.PERDIDAS_MAX:
            if cy_max >= config.CY_PERDIDA_CERCA:
                # Lo perdimos DESPUES de tenerlo bien abajo: se fue por el borde
                # inferior porque lo tenemos encima. Eso es haber llegado, no
                # haberlo perdido: fijamos la coordenada aca.
                break
            robot.drive(0, config.VEL_BUSQUEDA)   # perdida real: re-buscar girando
    wait(20)

# --- 3b. Centrar el objeto ANTES de fijar la coordenada ---
# El paso 3 frena mirando SOLO cy: cx no entra en la condicion, asi que el robot
# puede frenar a mitad de una correccion y quedar apuntando al costado. Como la
# coordenada se proyecta en la direccion del RUMBO, ese desvio la manda a un punto
# que no es donde esta el objeto.
#
# No se agrega cx a la condicion de frenado porque las dos podrian no cumplirse
# nunca a la vez y siempre cortaria por el tope de seguridad. En vez de eso:
# frenamos por cy y despues giramos EN EL LUGAR hasta centrar.
#
# Si el objeto ya no se ve, no hay nada que centrar: se salteo porque se fue por
# el borde inferior (lo tenemos encima), que es un final valido del paso 3.
reloj_centrado = StopWatch()
while reloj_centrado.time() < config.CENTRADO_FINAL_TIMEOUT:
    clase, conf, cx, area, cy = leer_camara()
    actualizar_pose()
    if not objeto_visible(clase, conf, area):
        break
    error = cx - config.CX_CENTRO
    if abs(error) <= config.CX_TOLERANCIA:
        break
    robot.drive(0, giro_centrado(error))
    wait(20)
robot.stop()

# --- 4. Fijar la posicion del objeto (todavia cerca, ANTES de despejar) ---
# Importante: calcular aca, con la pose en el punto de acercamiento. Si se calcula
# despues de la maniobra de despeje, la coordenada queda corrida.
rumbo = actualizar_pose()
# El objeto NO esta necesariamente justo delante: la camara no esta en la linea
# media del robot, asi que al "centrar" queda corrido al costado. Sumamos las dos
# componentes en el marco del robot:
#   adelante = (cos rumbo, sin rumbo)
#   derecha  = (-sin rumbo, cos rumbo)   <- +y es la derecha fisica
_adelante = config.OFFSET_OBJETO
_costado = config.OFFSET_OBJETO_LATERAL  # derecha(+) / izquierda(-)
obj_x = int(x + _adelante * cos(radians(rumbo)) - _costado * sin(radians(rumbo)))
obj_y = int(y + _adelante * sin(radians(rumbo)) + _costado * cos(radians(rumbo)))

# --- 5. Liberar la zona: salir de COSTADO del camino del recuperador ---
# El recuperador viaja del origen al objeto en linea recta. Retroceder dejaria al
# explorador sobre esa misma linea: el ultrasonido del recuperador lo veria a EL,
# frenaria antes de tiempo y cerraria la garra en el aire. Por eso pivota y sale
# perpendicular. El retroceso previo es solo para no rozar el objeto al girar.
robot.straight(-config.RETROCESO_PREVIO)
robot.turn(config.GIRO_DESPEJE)
robot.straight(config.DESPEJE_LATERAL)

# --- 6. Transmitir la coordenada del objeto ---
hub.display.char("T")
hub.speaker.beep()

# Transmitir varias veces (~5 s) para asegurar que el recuperador lo reciba.
for _ in range(50):
    radio.broadcast((obj_x, obj_y, clase_detectada))
    wait(100)

# Dejar de transmitir: un broadcast que sobrevive a la corrida hace que la
# SIGUIENTE arranque con el recuperador oyendo la coordenada de esta. El dato es
# valido, solo que viejo, asi que no se puede detectar mirando el contenido.
radio.broadcast(None)

hub.display.char("F")
