# config.py  (RECUPERADOR)
# ---------------------------------------------------------------------------
# Todos los numeros que se ajustan en la cancha viven aca. main.py los importa
# con `import config` y los usa. Si cambias de robot o de mision, tocas SOLO
# este archivo.
#
# Valores calibrados en cancha durante las pruebas de ubicacion
# (ver pruebas/test-ubicacion-recuperador.py y docs/calibracion.md).
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

# --- Garra: motor que ABRE/CIERRA la pinza (Port.C) ---
# OJO: en ESTE robot la pinza ABRE con velocidad + y CIERRA con velocidad -
# (al reves de lo tipico). main.py ya usa los signos correctos.
PUERTO_GARRA = Port.C
GARRA_VELOCIDAD = 300    # deg/s al abrir/cerrar la pinza
GARRA_DUTY_LIMIT = 90    # % de fuerza durante el cierre; mas alto = aprieta mas
GARRA_DUTY_SOSTEN = 100  # % de fuerza CONTINUA para mantener el objeto agarrado.
                         # run_until_stalled suelta la fuerza al terminar (coast);
                         # con dc() la garra sigue apretando mientras carga.

# --- Elevador: motor que SUBE/BAJA la garra (Port.D) ---
# No tiene tope arriba, pero en reposo queda ABAJO: esa posicion (donde queda al
# arrancar) es el cero. Subir = run_target(ELEVADOR_ANGULO_ARRIBA); bajar = 0.
PUERTO_ELEVADOR = Port.D
ELEVADOR_VELOCIDAD = 100      # deg/s
ELEVADOR_ANGULO_ARRIBA = -90  # deg desde "abajo" (0) hasta "levantada"
                              # (si baja en vez de subir, invertir el signo)

# --- Ultrasonido: confirma que el objeto esta al alcance de la garra (Port.E) ---
# El sensor esta a ~7 cm del punto de agarre, asi que un objeto justo en la garra
# se lee en ~DIST_AGARRE mm. Al llegar, si esta un poco lejos/cerca el robot se
# acerca/aleja en pasos chicos hasta entrar en rango.
PUERTO_ULTRASONIDO = Port.E
DIST_AGARRE = 60          # mm: lectura esperada con el objeto en la garra
TOLERANCIA_AGARRE = 15    # mm: dentro de esto se considera "en rango"
DIST_SIN_OBJETO = 250     # mm: mas alla de esto se asume que no hay objeto
PASO_CORRECCION = 20      # mm: correccion maxima de avance por intento
INTENTOS_AGARRE = 5       # cuantas veces reintenta acercarse antes de rendirse

# --- Posicion de arranque respecto del explorador ---
# Por defecto el recuperador arranca en el MISMO origen que el explorador
# (ver docs/contrato-datos.md) -> offset 0. Si en tu cancha arranca corrido
# (p.ej. 20 cm a la izquierda del explorador), poner el offset en el marco
# compartido. En estos robots turn() positivo gira a la IZQUIERDA, asi que
# "izquierda" = +y (ej.: 20 cm a la izquierda -> OFFSET_Y = 200).
OFFSET_X = 0    # mm: adelante(+)/atras(-) respecto del explorador
OFFSET_Y = -200    # mm: izquierda(+)/derecha(-) respecto del explorador
