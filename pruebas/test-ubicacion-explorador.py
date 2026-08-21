# test-ubicacion-explorador.py
# ---------------------------------------------------------------------------
# PRUEBA DE UBICACION (1 de 2)
#
# Escalon intermedio entre la prueba de canal (coordenada fija, sin moverse) y
# la mision completa con camara. Aca el explorador ELIGE un sitio al azar, MANEJA
# hasta ahi con su odometria y TRANSMITE esa coordenada. El recuperador
# (test-ubicacion-recuperador.py, en el otro hub) arranca de su posicion real,
# navega al punto y cierra la garra. Si las dos odometrias coinciden, la garra
# cierra donde el explorador dejo la marca.
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
from pybricks.tools import wait
from umath import atan2, degrees, sqrt
import urandom

# --- Parametros de la prueba ---
CANAL = 1                 # el mismo que escucha el recuperador
CLASE = 1                 # "clase" del objeto que va en la tupla transmitida
TX_MIN, TX_MAX = 300, 1000     # rango del sitio en x (mm, siempre adelante)
TY_MIN, TY_MAX = -400, 1000    # rango del sitio en y (mm, a los costados)
PAUSA_MARCA = 3000        # ms que espera en el sitio para que lo marques con cinta

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
motor_izq = Motor(Port.A, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.B, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=113)


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

# --- 2. Elegir un sitio al azar ---
tx = urandom.randint(TX_MIN, TX_MAX)
ty = urandom.randint(TY_MIN, TY_MAX)

# --- 3. Manejar hasta el sitio ---
robot.reset()
rumbo = degrees(atan2(ty, tx))
dist = sqrt(tx * tx + ty * ty)
robot.turn(rumbo)
robot.straight(dist)

# --- 4. Llego: avisar y dar una ventana para marcar el punto con cinta ---
# Marca el punto Y PONE EL OBJETO REAL ahi: el recuperador ahora hace la
# aproximacion final guiada por ultrasonido, asi que necesita algo que ver.
hub.speaker.beep()
hub.display.char("M")  # "M" de Marcar
print("Sitio: x=%d y=%d" % (tx, ty))
print("Marca el punto y PONE EL OBJETO ahi (el recuperador lo busca con el sensor).")
wait(PAUSA_MARCA)

# --- 5. Despejar el punto (al costado, NO hacia atras) ---
robot.straight(-RETROCESO_PREVIO)
robot.turn(GIRO_DESPEJE)
robot.straight(DESPEJE_LATERAL)

# --- 6. Transmitir el sitio en loop (asi el recuperador siempre lo oye) ---
hub.display.char("T")  # "T" de Transmitir
while True:
    radio.broadcast((tx, ty, CLASE))
    hub.light.on(Color.GREEN)
    wait(100)
    hub.light.off()
    wait(400)
