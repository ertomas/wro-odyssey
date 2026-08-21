# calibrar-garra.py
# ---------------------------------------------------------------------------
# CALIBRACION 3: GARRA_DUTY_LIMIT y GARRA_DUTY_SOSTEN  (RECUPERADOR, Port.C)
#
# Hace UN ciclo completo de la garra con el objeto real, sin mover el robot:
#   ABRIR -> (pausa para acomodar el objeto) -> CERRAR -> SOSTENER -> SOLTAR
#
# OJO: en ESTE robot la pinza ABRE con velocidad + y CIERRA con velocidad -
# (al reves de lo tipico). Los signos de abajo son los mismos que usa la mision.
#
# QUE MIRAR
#   - GARRA_DUTY_LIMIT (% de fuerza al cerrar): si el objeto SE RESBALA, subilo;
#     si lo APLASTA o el motor hace fuerza rara, bajalo.
#   - GARRA_DUTY_SOSTEN (% de fuerza continua): durante la pausa de sosten,
#     LEVANTA el robot y sacudilo suave. Si el objeto se escapa, subilo; si el
#     motor calienta, bajalo. run_until_stalled deja el motor en coast (fuerza
#     cero) al terminar, por eso hace falta el dc() o el objeto se cae al andar.
#
# Mantener en SYNC con recuperador/config.py.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait

# --- Valores actuales (SYNC con recuperador/config.py) ---
PUERTO_GARRA = Port.C
GARRA_VELOCIDAD = 300    # deg/s al abrir/cerrar
GARRA_DUTY_LIMIT = 90    # % de fuerza durante el cierre
GARRA_DUTY_SOSTEN = 100  # % de fuerza continua para mantener el objeto

PAUSA_ACOMODAR = 3000    # ms abierta, para poner el objeto entre las pinzas
PAUSA_SOSTEN = 5000      # ms sosteniendo: aca levantas y sacudis el robot

hub = PrimeHub()
garra = Motor(PUERTO_GARRA)

hub.display.char("G")  # "G" de Garra
print("duty_limit=%d  duty_sosten=%d" % (GARRA_DUTY_LIMIT, GARRA_DUTY_SOSTEN))

# --- ABRIR (velocidad +) ---
print("Abriendo...")
garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)
print("Abierta. Pone el objeto entre las pinzas.")
hub.speaker.beep()
wait(PAUSA_ACOMODAR)

# --- CERRAR (velocidad -) ---
print("Cerrando...")
garra.run_until_stalled(-GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)

# --- SOSTENER: run_until_stalled deja coast, dc() sigue apretando ---
garra.dc(-GARRA_DUTY_SOSTEN)
hub.display.char("S")  # "S" de Sosten
print("Sosteniendo. LEVANTA el robot y sacudilo: se cae el objeto?")
hub.speaker.beep(frequency=880, duration=400)
wait(PAUSA_SOSTEN)

# --- SOLTAR ---
print("Soltando...")
garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)

hub.display.char("F")  # "F" de Fin
