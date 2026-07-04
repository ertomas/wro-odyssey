# config.py  (RECUPERADOR)
# ---------------------------------------------------------------------------
# Todos los numeros que se ajustan en la cancha viven aca. main.py los importa
# con `import config` y los usa. Si cambias de robot o de mision, tocas SOLO
# este archivo.
# ---------------------------------------------------------------------------

from pybricks.parameters import Port, Direction

# --- Canal BLE (tiene que ser el MISMO que transmite el explorador) ---
CANAL = 1

# --- Hardware: puertos y geometria del robot ---
PUERTO_MOTOR_IZQ = Port.B
PUERTO_MOTOR_DER = Port.A
DIRECCION_MOTOR_IZQ = Direction.COUNTERCLOCKWISE  # el izquierdo suele ir invertido
DIRECCION_MOTOR_DER = Direction.CLOCKWISE

WHEEL_DIAMETER = 56   # mm  -> medir y calibrar (ver docs/calibracion.md)
AXLE_TRACK = 160      # mm  -> distancia entre las dos ruedas

# --- Garra: motor que abre/cierra la pinza ---
PUERTO_GARRA = Port.C
GARRA_VELOCIDAD = 300    # deg/s al cerrar la pinza
GARRA_DUTY_LIMIT = 50    # % de fuerza; mas alto = aprieta mas fuerte
