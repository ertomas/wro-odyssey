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
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.parameters import Color
from pybricks.tools import wait

# El canal (1) tiene que ser el mismo que escucha el recuperador.
hub = PrimeHub(broadcast_channel=1)

# Coordenada fija de prueba, en milimetros, mas la "clase" del objeto.
#   x = 300 mm hacia adelante, y = 200 mm hacia el costado, clase = 0
X, Y, CLASE = 300, 200, 0

hub.display.char("E")  # "E" de Explorador

while True:
    # Transmitir la tupla. El recuperador la recibe con hub.ble.observe(1).
    hub.ble.broadcast((X, Y, CLASE))

    # Parpadeo verde para ver que esta transmitiendo.
    hub.light.on(Color.GREEN)
    wait(100)
    hub.light.off()
    wait(400)
