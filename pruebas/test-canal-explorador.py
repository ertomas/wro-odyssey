# test-canal-explorador.py
# ---------------------------------------------------------------------------
# DEMO SIMPLE DE CANAL (1 de 2)
#
# Transmite una coordenada FIJA por BLE para probar la comunicacion hub-a-hub,
# sin camara ni nada mas. Corre este programa en un hub y
# `test-canal-recuperador.py` en el otro: el recuperador deberia oir la
# coordenada y manejar hacia ella.
#
# Si esto funciona, el canal broadcast/observe esta OK y recien ahi sumamos
# la camara y la odometria de verdad (ver explorador/ y recuperador/).
#
# Usa BLERadio (pybricks.messaging), la MISMA API que explorador/main.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.messaging import BLERadio
from pybricks.parameters import Color
from pybricks.tools import wait, StopWatch

# El canal (1) tiene que ser el mismo que escucha el recuperador.
CANAL = 1
TRANSMISION_MS = 60000  # ms transmitiendo, y despues PARA (libera el canal)

hub = PrimeHub()
radio = BLERadio(broadcast_channel=CANAL)

# Coordenada fija de prueba, en milimetros, mas la "clase" del objeto.
#   x = 300 mm hacia adelante, y = 200 mm hacia el costado, clase = 0
X, Y, CLASE = 300, 200, 0

hub.display.char("E")  # "E" de Explorador
print("Transmitiendo (%d, %d, %d) por el canal %d" % (X, Y, CLASE, CANAL))

# Transmitir por un rato ACOTADO y despues PARAR.
# Nunca dejar esto en bucle infinito: un broadcast que sobrevive a la corrida
# hace que la SIGUIENTE arranque con datos viejos, y el receptor sale hacia una
# coordenada de otra corrida. El dato es valido, solo que viejo, asi que no hay
# forma de detectarlo mirando el contenido. Por eso el receptor ademas exige
# silencio en el canal antes de aceptar nada: ARRANCAR SIEMPRE EL RECEPTOR
# PRIMERO y este despues.
reloj = StopWatch()
while reloj.time() < TRANSMISION_MS:
    # Transmitir la tupla. El recuperador la recibe con radio.observe(CANAL).
    radio.broadcast((X, Y, CLASE))

    # Parpadeo verde para ver que esta transmitiendo.
    hub.light.on(Color.GREEN)
    wait(100)
    hub.light.off()
    wait(400)

radio.broadcast(None)  # liberar el canal
hub.display.char("F")
print("Fin de la transmision: canal liberado.")
