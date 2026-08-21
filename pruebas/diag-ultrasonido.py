# diag-ultrasonido.py
# ---------------------------------------------------------------------------
# DIAGNOSTICO: por que el ultrasonido lee cerca cuando no hay nada
#
# Sintoma que diagnostica: en reposo el sensor lee >400 (vacio, correcto), pero
# apenas el robot arranca la lectura se cae a 55-70 y dispara el agarre. Hay
# tres causas posibles y cada una se arregla distinto:
#
#   A. La GARRA ABIERTA entra en el cono del sensor (los brazos se separan).
#      -> Se ve en la FASE 2 vs FASE 3: cerrada lee lejos, abierta lee cerca.
#      -> Arreglo: mover el sensor, o aproximarse con la garra CERRADA.
#
#   B. El conjunto garra/elevador SE BALANCEA con el tiron del arranque y cruza
#      el haz.
#      -> Se ve en la FASE 5: lee lejos parado, se cae al arrancar, y despues
#         se RECUPERA sola mientras avanza a velocidad constante.
#      -> Arreglo: filtrar los primeros ms de marcha (ya esta en la mision), o
#         rigidizar el montaje.
#
#   C. El robot CABECEA al acelerar y el sensor apunta al piso.
#      -> Igual que B en la FASE 5, pero la caida es mas corta y mas profunda.
#      -> Arreglo: bajar la aceleracion, subir/inclinar el sensor.
#
#   Si lee cerca SIEMPRE, en todas las fases -> el sensor esta viendo una parte
#   fija del robot. No hay arreglo por software: hay que moverlo.
#
# NO agarra nada y solo avanza AVANCE_PRUEBA mm. Dejar el frente LIBRE: la
# gracia es leer el vacio, cualquier objeto adelante arruina el diagnostico.
#
# Mantener en SYNC con recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, UltrasonicSensor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# --- Parametros del diagnostico ---
AVANCE_PRUEBA = 300    # mm que avanza en la fase de marcha (frente LIBRE)
VEL_MARCHA = 40        # mm/s, la misma VEL_APROXIMACION de la mision
LECTURAS_FASE = 10     # lecturas por fase estatica
INTERVALO = 200        # ms entre lecturas estaticas

# --- Hardware (SYNC con recuperador/config.py) ---
WHEEL_DIAMETER = 56
AXLE_TRACK = 164
GARRA_VELOCIDAD = 300
GARRA_DUTY_LIMIT = 90
ELEVADOR_VELOCIDAD = 100
ELEVADOR_ANGULO_ARRIBA = -90

hub = PrimeHub()
motor_izq = Motor(Port.B, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.A, Direction.CLOCKWISE)
robot = DriveBase(motor_izq, motor_der,
                  wheel_diameter=WHEEL_DIAMETER, axle_track=AXLE_TRACK)
garra = Motor(Port.C)
elevador = Motor(Port.D)
ultrasonido = UltrasonicSensor(Port.E)


def medir(etiqueta):
    """Toma LECTURAS_FASE lecturas quietas y reporta min/max/mediana."""
    lecturas = []
    for _ in range(LECTURAS_FASE):
        lecturas.append(ultrasonido.distance())
        wait(INTERVALO)
    ordenadas = sorted(lecturas)
    print("%s: min=%d max=%d mediana=%d" %
          (etiqueta, ordenadas[0], ordenadas[-1], ordenadas[len(ordenadas) // 2]))
    print("   %s" % lecturas)
    return ordenadas[len(ordenadas) // 2]


hub.display.char("D")  # "D" de Diagnostico
print("--- diag-ultrasonido ---")
print("DEJAR EL FRENTE LIBRE. Todo lo que sigue deberia leer LEJOS.")
print("")

elevador.reset_angle(0)

# --- FASE 1: como esta, sin tocar nada ---
m1 = medir("1. reposo (como quedo)")

# --- FASE 2: garra CERRADA, elevador abajo ---
garra.run_until_stalled(-GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)
garra.stop()
m2 = medir("2. garra CERRADA, elevador abajo")

# --- FASE 3: garra ABIERTA, elevador abajo  <- la clave para la causa A ---
garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)
garra.stop()
m3 = medir("3. garra ABIERTA, elevador abajo")

# --- FASE 4: garra abierta, elevador ARRIBA ---
elevador.run_target(ELEVADOR_VELOCIDAD, ELEVADOR_ANGULO_ARRIBA)
m4 = medir("4. garra ABIERTA, elevador ARRIBA")
elevador.run_target(ELEVADOR_VELOCIDAD, 0)

# --- FASE 5: EN MARCHA, garra abierta (el estado real de la aproximacion) ---
# Imprime lectura + odometria juntas: si la lectura se cae al arrancar y despues
# se recupera sola, es balanceo o cabeceo (B/C). Si se queda caida, es la garra
# o el chasis metido en el haz (A / fijo).
print("")
print("5. EN MARCHA (garra abierta). odometria_mm : lectura_mm")
robot.reset()
robot.drive(VEL_MARCHA, 0)
while robot.distance() < AVANCE_PRUEBA:
    print("   %d : %d" % (robot.distance(), ultrasonido.distance()))
    wait(50)
robot.stop()

# --- FASE 6: recien frenado (el momento en que la mision re-mide quieto) ---
m6 = medir("6. recien frenado")

# --- Volver al punto de partida ---
robot.straight(-robot.distance())

print("")
print("--- RESUMEN ---")
print("reposo=%d  cerrada=%d  abierta=%d  elevador_arriba=%d  frenado=%d"
      % (m1, m2, m3, m4, m6))
print("Si ABIERTA << CERRADA -> la garra abierta entra en el haz (causa A).")
print("Si todas lejos pero la FASE 5 se cae al arrancar y se recupera ->")
print("   balanceo o cabeceo (causa B/C): lo filtra el asentamiento.")
print("Si TODAS leen cerca -> el sensor ve una parte fija del robot: moverlo.")
hub.display.char("F")
