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
SILENCIOS_CANAL_LIBRE = 10  # lecturas seguidas SIN datos antes de aceptar una
                            # coordenada. Sirve para descartar un broadcast VIEJO:
                            # si el explorador de una corrida anterior quedo
                            # transmitiendo, aceptarlo mandaria el robot al sitio
                            # de esa corrida. Exigir silencio primero garantiza que
                            # la coordenada empezo DESPUES de que nos pusimos a oir.

# --- Hardware: puertos y geometria del robot ---
PUERTO_MOTOR_IZQ = Port.B
PUERTO_MOTOR_DER = Port.A
DIRECCION_MOTOR_IZQ = Direction.COUNTERCLOCKWISE  # el izquierdo suele ir invertido
DIRECCION_MOTOR_DER = Direction.CLOCKWISE

WHEEL_DIAMETER = 56   # mm  -> calibrado 2026-08-20 (800 pedidos -> 798 reales)
AXLE_TRACK = 164      # mm  -> calibrado 2026-08-20 con el ensayo de 3 vueltas.
                      # NO es la medida con regla (esa da 161): al pivotar los
                      # neumaticos restriegan y hay que declarar un track mayor
                      # para compensar. Ver docs/calibracion.md.

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

# --- Ultrasonido + aproximacion final (Port.E) ---
# MEDIDO EN CANCHA 2026-08-20 (ver docs/calibracion.md):
#   - Lecturas confiables solo de 54 mm para arriba. Mas cerca el sensor se
#     CLAVA en 40 (ese 40 no es una medicion: es el piso del sensor) y salta
#     erraticamente entre 40 y 65.
#   - La garra agarra bien hasta una lectura de 55.
#   - Mirando al vacio lee >400.
# O sea: la zona confiable (>=54) y la ventana de captura (<=55) se solapan en
# 1 mm. NO se puede usar el sensor para decidir "el objeto esta en la garra".
#
# POR ESO la aproximacion final va en DOS TRAMOS:
#   1. Avanzar despacio hasta DETECTAR el objeto a UMBRAL_DETECCION, que esta
#      bien dentro de la zona confiable del sensor.
#   2. Frenar, RE-MEDIR QUIETO (mediana de varias lecturas) y cubrir el resto
#      con ODOMETRIA hasta dejar el objeto a DIST_OBJETIVO_FINAL.
# El re-medido quieto absorbe el sobrepaso del frenado, asi que el avance final
# se calcula desde la posicion REAL. Sobre ~100 mm la odometria calibrada tiene
# error submilimetrico: mucho mejor que el sensor a esa distancia.
PUERTO_ULTRASONIDO = Port.E
DIST_MIN_CONFIABLE = 54     # mm: por debajo de esto la lectura no sirve (referencia)
UMBRAL_DETECCION = 150      # mm: lectura a la que se da por detectado el objeto.
                            # 3x el minimo confiable y 1/3 de la lectura en vacio.
DIST_OBJETIVO_FINAL = 45    # mm: donde queremos dejar el objeto antes de cerrar.
                            # Centro de la ventana de captura (agarra hasta 55).
ESPERA_ASENTAMIENTO = 400   # ms de marcha antes de creerle al sensor. El tiron del
                            # arranque hace saltar la lectura de >400 a 55-70 (se
                            # balancea la garra / cabecea el chasis) y eso disparaba
                            # el agarre al instante. A 40 mm/s son ~16 mm: inofensivo.
CONFIRMACIONES_DETECCION = 3  # lecturas SEGUIDAS bajo el umbral para dar por detectado.
                            # Una sola lectura es un pico; tres seguidas es un objeto.
LECTURAS_CONFIRMACION = 5   # lecturas quietas antes del tramo final; se usa la MEDIANA
MARGEN_CONFIRMACION = 50    # mm: si al re-medir quieto da mas de UMBRAL+esto, lo que
                            # vimos en movimiento era ruido -> se rinde, no agarra
MARGEN_APROXIMACION = 300   # mm antes de la coordenada donde deja de manejar a ciegas.
                            # Tiene que ser MAS GRANDE que el error radial del
                            # explorador, o el robot embiste el objeto a velocidad
                            # de crucero antes de empezar a mirar el sensor.
VEL_APROXIMACION = 40       # mm/s del tramo de busqueda. Ahora que el frenado se
                            # auto-corrige con el re-medido quieto, se puede subir
                            # para ganar tiempo de mision (probar de a poco).
CREEP_MAX = 550             # mm max de avance lento buscando el objeto (si no aparece, se rinde)

# --- Posicion de arranque respecto del explorador ---
# Por defecto el recuperador arranca en el MISMO origen que el explorador
# (ver docs/contrato-datos.md) -> offset 0. Si en tu cancha arranca corrido
# (p.ej. 16.5 cm a la izquierda del explorador), poner el offset en el marco
# compartido.
#
# SIGNO DE +Y (verificado 2026-08-20, ver docs/setup-cancha.md):
# turn() positivo gira a la DERECHA (horario), que es la convencion estandar de
# Pybricks. El explorador integra su pose con y += paso*sin(rumbo) usando ese
# mismo rumbo, asi que en el marco compartido +y es la DERECHA fisica.
#   -> derecha = +y   |   izquierda = -y
# El recuperador arranca a la IZQUIERDA del explorador, o sea en y NEGATIVO.
OFFSET_X = 0      # mm: adelante(+)/atras(-) respecto del explorador
OFFSET_Y = -165   # mm: derecha(+)/izquierda(-) respecto del explorador.
                  # 165 mm a la IZQUIERDA -> -165.
