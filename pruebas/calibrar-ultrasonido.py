# calibrar-ultrasonido.py
# ---------------------------------------------------------------------------
# CALIBRACION 2: rango util del ultrasonido  (solo RECUPERADOR, Port.E)
#
# Este programa NO mueve nada: solo imprime la lectura en loop para que midas
# con el objeto en la mano.
#
# LO IMPORTANTE: el ultrasonido NO sirve cerca. Por debajo de cierta distancia
# se CLAVA en un valor de piso (en este robot, 40) y salta erraticamente. Ese
# valor de piso NO es una medicion. Por eso la mision no usa el sensor para
# decidir "el objeto esta en la garra": lo usa para DETECTAR lejos, donde ve
# bien, y remata el ultimo tramo con odometria (ver docs/calibracion.md).
#
# QUE MEDIR
#   1. RANGO CONFIABLE: pone el objeto lejos y acercalo de a poco. Anota a
#      partir de que lectura EMPIEZA a saltar / se clava. Todo lo que este por
#      debajo de eso no sirve. -> DIST_MIN_CONFIABLE
#   2. CANCHA VACIA: saca el objeto y anota que lee al vacio. UMBRAL_DETECCION
#      tiene que quedar bien por DEBAJO de esto (si no, frena creyendo que
#      llego) y bien por ENCIMA de DIST_MIN_CONFIABLE.
#   3. VENTANA DE CAPTURA (con calibrar-garra.py, no con este programa): pone el
#      objeto en el punto de agarre, cerra la garra y confirma; despues alejalo
#      de a 10 mm hasta que falle. DIST_OBJETIVO_FINAL va al MEDIO del rango
#      que funciono.
#
# Cada lectura muestra si CON LOS VALORES ACTUALES el robot daria el objeto por
# detectado ahi, y si la lectura cae en la zona no confiable.
#
# Mantener en SYNC con recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import UltrasonicSensor
from pybricks.parameters import Port
from pybricks.tools import wait

# --- Valores actuales (SYNC con recuperador/config.py) ---
PUERTO_ULTRASONIDO = Port.E
DIST_MIN_CONFIABLE = 54  # mm: por debajo de esto la lectura no sirve
UMBRAL_DETECCION = 150   # mm: la mision da el objeto por detectado en esta lectura

INTERVALO = 300         # ms entre lecturas

hub = PrimeHub()
ultrasonido = UltrasonicSensor(PUERTO_ULTRASONIDO)

hub.display.char("U")  # "U" de Ultrasonido
print("Umbral de deteccion actual: %d mm | minimo confiable: %d mm"
      % (UMBRAL_DETECCION, DIST_MIN_CONFIABLE))
print("Acerca el objeto de a poco y anota donde EMPIEZA a saltar.")

while True:
    d = ultrasonido.distance()
    if d < DIST_MIN_CONFIABLE:
        print("%d mm  <- NO CONFIABLE (zona muerta del sensor)" % d)
    elif d <= UMBRAL_DETECCION:
        print("%d mm  <- DETECTADO (aca frenaria la mision)" % d)
    else:
        print("%d mm" % d)
    wait(INTERVALO)
