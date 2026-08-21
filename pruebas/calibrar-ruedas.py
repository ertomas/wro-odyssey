# calibrar-ruedas.py
# ---------------------------------------------------------------------------
# CALIBRACION 1: WHEEL_DIAMETER y AXLE_TRACK
#
# Sirve para CUALQUIERA de los dos robots: elegi el robot en ROBOT y el ensayo
# en MODO. Es el PRIMER paso de la calibracion: si las ruedas estan mal, todo
# lo demas (navegacion, ultrasonido, garra) se calibra sobre una base torcida.
#
# COMO USARLO
#   MODO = "recta"  -> avanza 1000 mm. Marca con cinta donde arranca, medi lo
#                      que avanzo DE VERDAD y ajusta:
#                          nuevo_diametro = actual * (1000 / avanzo_real)
#                      Repeti hasta que 1000 mm sean 1000 mm (+-5 mm).
#
#   MODO = "giro"   -> gira VUELTAS_GIRO vueltas. Marca el frente del robot con
#                      una linea en el piso y estima cuantos grados giro DE
#                      VERDAD en total. Ajusta:
#                          nuevo_axle = actual * (grados_pedidos / grados_reales)
#                      DriveBase calcula el arco de las ruedas a partir del
#                      axle_track declarado, asi que:
#                          SUBIR axle_track -> gira MAS
#                          BAJAR axle_track -> gira MENOS
#                      Calibra la recta PRIMERO: el giro se apoya en el diametro.
#
#   MODO = "signo"  -> gira 90 grados una sola vez, para confirmar hacia que
#                      lado gira el positivo. Lo ESPERADO es DERECHA (horario):
#                      es la convencion estandar de Pybricks y es la que asume
#                      todo el codigo. De ahi sale que en el marco compartido
#                      +y sea la DERECHA fisica, y por eso el recuperador (que
#                      arranca a la izquierda) lleva OFFSET_Y NEGATIVO.
#                      Si girara a la IZQUIERDA, algun Direction de los motores
#                      esta invertido o los puertos izq/der estan cruzados.
#
# Los valores de abajo tienen que quedar en SYNC con el config.py del robot que
# estes calibrando. Cuando termines, copialos al config.py y anotalos en la
# tabla de docs/calibracion.md.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# --- Que robot y que ensayo ---
ROBOT = "recuperador"   # "recuperador" o "explorador"
MODO = "signo"          # "recta", "giro" o "signo"

DISTANCIA_RECTA = 800   # mm del ensayo de recta. Cuanto mas largo, mejor promedia
                        # el error, pero tiene que ENTRAR en la pista con margen:
                        # en la primera corrida el robot se puede pasar. Con una
                        # pista de 1 m, 800 deja 200 mm de colchon. Si tenes mas
                        # lugar, subilo a 1000.
VUELTAS_GIRO = 3        # vueltas completas del ensayo de giro. Una sola vuelta deja
                        # un error demasiado chico para medirlo a ojo; con 3 se
                        # triplica y se ve claro contra la linea del piso.
PAUSA_INICIAL = 2000    # ms antes de moverse, para soltar el robot y sacar la mano

# --- Valores actuales por robot (SYNC con el config.py de cada carpeta) ---
if ROBOT == "recuperador":
    PUERTO_IZQ, PUERTO_DER = Port.B, Port.A
    WHEEL_DIAMETER = 56
    AXLE_TRACK = 164  # medido con regla: 161. El calibrado sale mayor por el
                      # patinaje al pivotar (ver docs/calibracion.md).
else:
    PUERTO_IZQ, PUERTO_DER = Port.A, Port.B
    WHEEL_DIAMETER = 56
    AXLE_TRACK = 113

hub = PrimeHub()
motor_izq = Motor(PUERTO_IZQ, Direction.COUNTERCLOCKWISE)
motor_der = Motor(PUERTO_DER, Direction.CLOCKWISE)
robot = DriveBase(
    motor_izq, motor_der,
    wheel_diameter=WHEEL_DIAMETER,
    axle_track=AXLE_TRACK,
)

hub.display.char("C")  # "C" de Calibrar (antes de mover: si se traba, fue el movimiento)
print("Robot: %s | modo: %s" % (ROBOT, MODO))
print("wheel_diameter=%d  axle_track=%d" % (WHEEL_DIAMETER, AXLE_TRACK))

# Ventana para soltar el robot y sacar la mano antes de que arranque.
wait(PAUSA_INICIAL)
robot.reset()

if MODO == "recta":
    robot.straight(DISTANCIA_RECTA)
    print("Pedi %d mm. Medi con regla cuanto avanzo de VERDAD." % DISTANCIA_RECTA)
    print("Ajuste: nuevo = %d * (%d / avanzo_real)" % (WHEEL_DIAMETER, DISTANCIA_RECTA))
elif MODO == "giro":
    grados = 360 * VUELTAS_GIRO
    robot.turn(grados)
    print("Pedi %d grados (%d vueltas)." % (grados, VUELTAS_GIRO))
    print("Estima cuantos giro DE VERDAD y ajusta:")
    print("  nuevo = %d * (%d / grados_reales)" % (AXLE_TRACK, grados))
    print("Giro de MENOS -> subi axle_track. Giro de MAS -> bajalo.")
else:  # "signo"
    robot.turn(90)
    print("Pedi +90 grados. Lo ESPERADO es que gire a la DERECHA (horario).")
    print("Derecha -> todo OK: en el marco compartido +y es la DERECHA fisica,")
    print("  asi que el robot que arranca a la IZQUIERDA lleva OFFSET_Y NEGATIVO.")
    print("Izquierda -> algun Direction esta invertido o los puertos izq/der")
    print("  estan cruzados. Revisa config.py ANTES de tocar OFFSET_Y.")

hub.speaker.beep()
hub.display.char("F")  # "F" de Fin
