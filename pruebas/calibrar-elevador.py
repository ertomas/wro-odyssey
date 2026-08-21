# calibrar-elevador.py
# ---------------------------------------------------------------------------
# CALIBRACION 4: ELEVADOR_ANGULO_ARRIBA  (RECUPERADOR, Port.D)
#
# El elevador NO tiene tope arriba, pero en reposo queda ABAJO: esa posicion al
# arrancar es el CERO. Subir = run_target(ELEVADOR_ANGULO_ARRIBA), bajar = 0.
#
# ANTES DE CORRER: deja la garra en su REPOSO ABAJO. El programa fija el cero
# ahi. Si arrancas con el elevador a media altura, todo el recorrido queda
# corrido.
#
# QUE MIRAR
#   - Si BAJA en vez de subir -> INVERTI EL SIGNO de ELEVADOR_ANGULO_ARRIBA.
#     Es el error mas comun: esta empujando contra el tope de abajo.
#   - Ajusta la MAGNITUD para que levante el objeto lo justo, sin forzar.
#   - Repeti la prueba CON EL OBJETO AGARRADO (peso real): un elevador que sube
#     vacio puede no llegar cargado.
#
# Mantener en SYNC con recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait

# --- Valores actuales (SYNC con recuperador/config.py) ---
PUERTO_ELEVADOR = Port.D
ELEVADOR_VELOCIDAD = 100      # deg/s
ELEVADOR_ANGULO_ARRIBA = -90  # deg desde "abajo" (0) hasta "levantada"

PAUSA_ARRIBA = 3000  # ms arriba, para mirar la altura que quedo
CICLOS = 2           # cuantas veces sube y baja

hub = PrimeHub()
elevador = Motor(PUERTO_ELEVADOR)

hub.display.char("E")  # "E" de Elevador
print("angulo_arriba=%d  velocidad=%d" % (ELEVADOR_ANGULO_ARRIBA, ELEVADOR_VELOCIDAD))
print("El cero es DONDE ESTA AHORA (reposo abajo).")

# El reposo actual es el cero de todo el recorrido.
elevador.reset_angle(0)

for ciclo in range(CICLOS):
    print("Ciclo %d: subiendo a %d..." % (ciclo, ELEVADOR_ANGULO_ARRIBA))
    elevador.run_target(ELEVADOR_VELOCIDAD, ELEVADOR_ANGULO_ARRIBA)
    print("Arriba. Angulo real: %d. Subio o bajo?" % elevador.angle())
    hub.speaker.beep(frequency=880, duration=200)
    wait(PAUSA_ARRIBA)

    print("Bajando a 0...")
    elevador.run_target(ELEVADOR_VELOCIDAD, 0)
    print("Abajo. Angulo real: %d" % elevador.angle())
    wait(1000)

hub.display.char("F")  # "F" de Fin
