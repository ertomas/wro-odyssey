# config.py  (EXPLORADOR)
# ---------------------------------------------------------------------------
# Todos los numeros que se ajustan en la cancha viven aca. main.py los importa
# con `import config` y los usa. Si cambias de robot o de mision, tocas SOLO
# este archivo.
# ---------------------------------------------------------------------------

from pybricks.parameters import Port, Direction

# --- Canal BLE (tiene que ser el MISMO en el recuperador) ---
CANAL = 1

# --- Hardware: puertos y geometria del robot ---
PUERTO_MOTOR_IZQ = Port.A
PUERTO_MOTOR_DER = Port.B
DIRECCION_MOTOR_IZQ = Direction.COUNTERCLOCKWISE  # el izquierdo suele ir invertido
DIRECCION_MOTOR_DER = Direction.CLOCKWISE

WHEEL_DIAMETER = 56   # mm  -> medir y calibrar (ver docs/calibracion.md)
AXLE_TRACK = 113      # mm  -> distancia entre las dos ruedas

# --- Deteccion: que objeto(s) buscamos y cuando le creemos ---
# Indices de las clases del modelo Teachable Machine que cuentan como "objetivo".
# El modelo incluido tiene: 0=egipto, 1=Panama, 2=Suelo. Vale CUALQUIERA de la
# lista (ej.: (0, 1) = egipto o Panama). Para una sola clase, dejar (1,).
CLASES_OBJETIVO = (0, 1)
CONFIANZA_MIN = 70    # % minimo de certeza para creerle a la prediccion

# --- Centrado visual (donde queremos el objeto dentro de la imagen) ---
CX_CENTRO = 50        # 50 = centro de la imagen
CX_TOLERANCIA = 8     # margen aceptable alrededor del centro
KP_CENTRADO = 1.5     # ganancia proporcional del giro al centrar

# --- Acercamiento ---
AREA_CERCA = 45       # area (0..100) a la que consideramos "ya estoy cerca"
OFFSET_OBJETO = 60    # mm extra delante del robot donde queda el objeto

# --- Velocidades de maniobra ---
VEL_BUSQUEDA = 30     # deg/s girando en el lugar para buscar
VEL_ACERCAMIENTO = 120  # mm/s avanzando hacia el objeto
