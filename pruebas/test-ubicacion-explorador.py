# test-ubicacion-explorador.py
# ---------------------------------------------------------------------------
# PRUEBA DE UBICACION (1 de 2)
#
# Escalon intermedio entre la prueba de canal (coordenada fija, sin moverse) y
# la mision completa con camara. Aca el explorador MANEJA un recorrido al azar,
# calcula donde estaria el OBJETO y TRANSMITE esa coordenada. El recuperador
# (test-ubicacion-recuperador.py, en el otro hub) arranca de su posicion real,
# navega al punto y cierra la garra. Si las dos odometrias coinciden, la garra
# cierra donde el explorador dejo la marca.
#
# EL RECORRIDO ES: recto AVANCE_PREVIO -> giro al azar a la IZQUIERDA (0..GIRO_MAX)
# -> recto al azar (AVANCE_MIN..AVANCE_MAX). El primer tramo recto existe para no
# maniobrar pegado al recuperador, que arranca al lado: girando en el sitio de
# arranque a veces lo chocaba o se salia de la pista.
#
# EL OBJETO NO VA DEBAJO DEL ROBOT. Va OFFSET_OBJETO adelante y
# OFFSET_OBJETO_LATERAL al costado de la pose final, que es donde apunta la
# camara en la mision. Antes este test transmitia la pose pelada (el medio del
# eje), asi que el recuperador iba a buscar el objeto justo donde estaba parado
# el explorador -- y sobre todo NO ejercitaba la cuenta de los offsets, que es la
# misma que hace explorador/main.py.
#
# Arranca solo (sin apretar botones) apenas se sube el programa.
#
# Origen: el robot arranca en (0, 0) mirando hacia +x (adelante = 0 grados).
# Este archivo es autocontenido (no importa config.py). Los valores de hardware
# de abajo tienen que quedar en SYNC con explorador/config.py.
#
# Usa BLERadio (pybricks.messaging), la MISMA API que explorador/main.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.messaging import BLERadio
from pybricks.parameters import Port, Direction, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch
from umath import cos, sin, radians
import urandom

# --- Parametros de la prueba ---
CANAL = 1                 # el mismo que escucha el recuperador
CLASE = 1                 # "clase" del objeto que va en la tupla transmitida
PAUSA_MARCA = 3000        # ms que espera en el sitio para que lo marques con cinta
TRANSMISION_MS = 30000    # ms transmitiendo el sitio, y DESPUES PARA. Nunca dejarlo
                          # en bucle infinito: un broadcast que sobrevive a la
                          # corrida hace que la SIGUIENTE arranque con datos viejos.

# --- Recorrido hasta el sitio ---
# ANTES elegia un (tx, ty) al azar y giraba en el lugar de arranque para encararlo.
# Ahi el explorador tiene al recuperador AL LADO: a veces lo chocaba o se salia de
# la pista. Ahora primero se despega en linea recta y recien despues gira.
AVANCE_PREVIO = 300       # mm en linea antes de girar: saca al explorador de al lado
                          # del recuperador antes de que empiece a maniobrar
GIRO_MAX = 90             # grados max del giro al azar hacia la IZQUIERDA (0..GIRO_MAX).
                          # Siempre a la izquierda porque el recuperador arranca a ese
                          # lado: asi el sitio le queda de frente y no cruzado.
AVANCE_MIN, AVANCE_MAX = 200, 400   # mm que avanza despues de girar, al azar

# --- Donde queda el objeto respecto del explorador (SYNC con explorador/config.py) ---
# La mision NO transmite su propia pose: transmite la del OBJETO, que la camara ve
# adelante y al costado (la camara no esta en la linea media del robot). Este test
# simula lo mismo, asi el objeto va DELANTE del explorador --como en la mision-- y
# no debajo de sus ruedas. Ademas ejercita la misma cuenta que hace main.py.
OFFSET_OBJETO = 150          # mm adelante (componente sobre el rumbo)
OFFSET_OBJETO_LATERAL = -65  # mm al costado: derecha(+) / izquierda(-)

# --- Despeje: misma maniobra que la mision (explorador/main.py paso 5) ---
# Retroceder EN LINEA dejaria al explorador sobre el camino origen->sitio, justo
# por donde despues pasa el recuperador: su ultrasonido veria al EXPLORADOR en
# vez del objeto, frenaria antes y cerraria la garra en el aire. Por eso se corre
# de COSTADO. SYNC con RETROCESO_PREVIO / GIRO_DESPEJE / DESPEJE_LATERAL.
RETROCESO_PREVIO = 150    # mm hacia atras antes de pivotar (para no rozar el objeto)
GIRO_DESPEJE = 90         # grados hacia el costado LIBRE (invertir el signo si es el otro)
DESPEJE_LATERAL = 500     # mm perpendiculares al camino del recuperador

# --- Hardware calibrado (SYNC con explorador/config.py) ---
hub = PrimeHub()
radio = BLERadio(broadcast_channel=CANAL)
motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)  # recableado 2026-08-20
motor_der = Motor(Port.A, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=112)


def sembrar_azar():
    """Siembra el RNG con el ruido del IMU para que el sitio varie por corrida.

    Sin semilla el "aleatorio" repetiria la misma secuencia en cada arranque.
    Acumular varias lecturas del acelerometro (quieto ~9810 mm/s2 en z, con
    ruido en los ultimos digitos) da suficiente variacion: basta con que la
    semilla cambie en 1 para que randint entregue otra secuencia.
    """
    semilla = 0
    for _ in range(10):
        ax, ay, az = hub.imu.acceleration()
        semilla += int(abs(ax) + abs(ay) + abs(az))
        wait(5)
    urandom.seed(semilla)


hub.display.char("E")  # "E" de Explorador

# --- 1. Sembrar el azar (sin botones) ---
sembrar_azar()

# --- 2. Manejar hasta un sitio al azar ---
# El recorrido es: RECTO -> girar a la izquierda al azar -> RECTO. El primer tramo
# recto es lo que evita maniobrar pegado al recuperador.
robot.reset()

# 2a. Despegarse antes de girar.
robot.straight(AVANCE_PREVIO)
d1 = robot.distance()          # lo que avanzo DE VERDAD en el primer tramo

# 2b. Girar a la IZQUIERDA un angulo al azar.
# OJO CON EL SIGNO: turn() positivo gira a la DERECHA (horario). Izquierda es
# NEGATIVO. Ver docs/setup-cancha.md.
giro = urandom.randint(0, GIRO_MAX)
robot.turn(-giro)
rumbo = robot.angle()          # rumbo REAL despues del giro

# 2c. Avanzar hasta el sitio.
avance = urandom.randint(AVANCE_MIN, AVANCE_MAX)
robot.straight(avance)
d2 = robot.distance() - d1     # avance REAL del segundo tramo

# --- 3. Calcular la pose y, desde ella, el sitio del OBJETO ---
# La pose sale de la ODOMETRIA REAL (d1, rumbo, d2), NO de los valores pedidos:
# si el giro se queda corto, el robot queda donde quedo, y mandar el angulo
# teorico apuntaria a un punto que no existe. La mision hace lo mismo con
# actualizar_pose().
px = d1 + d2 * cos(radians(rumbo))
py = d2 * sin(radians(rumbo))

# El objeto NO esta en la pose del robot: esta adelante y al costado, igual que
# en la mision (explorador/main.py). Misma descomposicion:
#   adelante = (cos rumbo, sin rumbo)
#   derecha  = (-sin rumbo, cos rumbo)   <- +y es la derecha fisica
tx = int(px + OFFSET_OBJETO * cos(radians(rumbo))
            - OFFSET_OBJETO_LATERAL * sin(radians(rumbo)))
ty = int(py + OFFSET_OBJETO * sin(radians(rumbo))
            + OFFSET_OBJETO_LATERAL * cos(radians(rumbo)))

# --- 4. Llego: avisar y dar una ventana para marcar el punto con cinta ---
# El objeto NO va debajo del robot: va DELANTE, donde lo veria la camara.
hub.speaker.beep()
hub.display.char("M")  # "M" de Marcar
print("Pedido: recto %d -> giro %d izq -> recto %d" % (AVANCE_PREVIO, giro, avance))
print("Real:   recto %d -> rumbo %d      -> recto %d" % (d1, rumbo, d2))
print("Pose del robot (medio del eje): x=%d y=%d" % (int(px), int(py)))
print("Sitio del OBJETO:               x=%d y=%d" % (tx, ty))
print("")
if OFFSET_OBJETO_LATERAL < 0:
    _lado = "IZQUIERDA"
else:
    _lado = "DERECHA"
print("MARCA el objeto a %d mm ADELANTE y %d mm a la %s"
      % (OFFSET_OBJETO, abs(OFFSET_OBJETO_LATERAL), _lado))
print("del MEDIO DEL EJE: ahi es donde apunta la camara en la mision.")
print("Ponelo cuando el explorador se haya corrido (tenes toda la transmision).")
wait(PAUSA_MARCA)

# --- 5. Despejar el punto (al costado, NO hacia atras) ---
robot.straight(-RETROCESO_PREVIO)
robot.turn(GIRO_DESPEJE)
robot.straight(DESPEJE_LATERAL)

# --- 6. Transmitir el sitio, POR UN RATO ACOTADO ---
# OJO: antes esto era un `while True` que transmitia PARA SIEMPRE. Con eso, al
# arrancar la corrida SIGUIENTE el hub seguia transmitiendo el sitio de la
# anterior: el recuperador lo agarraba al instante y salia hacia un punto viejo,
# antes de que el explorador se moviera. Cada eslabon "andaba" por separado y el
# integrado fallaba igual, sin correlacion con nada de la corrida en curso.
#
# La mision transmite ~5 s y para (explorador/main.py). Aca damos mas margen
# porque hay que acomodar el objeto, pero SIEMPRE termina y libera el canal.
hub.display.char("T")  # "T" de Transmitir
reloj_tx = StopWatch()
while reloj_tx.time() < TRANSMISION_MS:
    radio.broadcast((tx, ty, CLASE))
    hub.light.on(Color.GREEN)
    wait(100)
    hub.light.off()
    wait(400)

radio.broadcast(None)  # dejar de transmitir: libera el canal para la proxima corrida
hub.display.char("F")  # "F" de Fin
print("Fin de la transmision: canal liberado.")
