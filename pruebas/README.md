# Pruebas y calibración

Programas sueltos para calibrar y depurar cada parte por separado, sin depender
de la misión completa. Todos son **autocontenidos** (no importan `config.py`):
los valores están duplicados arriba de cada archivo y hay que mantenerlos en
**sync** con el `config.py` del robot correspondiente.

Se suben con [Pybricks Code](https://code.pybricks.com) como archivo suelto —
no hace falta armar un proyecto multi-archivo.

## Calibración (recuperador, de a uno por vez)

Corrélos **en este orden**: si las ruedas están mal, todo lo demás se calibra
sobre una base torcida.

| Archivo | Qué calibra | Config |
|---------|-------------|--------|
| [`calibrar-ruedas.py`](calibrar-ruedas.py) | `WHEEL_DIAMETER`, `AXLE_TRACK` | ambos robots (elegí en `ROBOT`) |
| [`calibrar-ultrasonido.py`](calibrar-ultrasonido.py) | `DIST_MIN_CONFIABLE`, `UMBRAL_DETECCION` | recuperador |
| [`diag-ultrasonido.py`](diag-ultrasonido.py) | *(no calibra: diagnostica)* | recuperador |
| [`calibrar-garra.py`](calibrar-garra.py) | `GARRA_DUTY_LIMIT`, `GARRA_DUTY_SOSTEN` | recuperador |
| [`calibrar-elevador.py`](calibrar-elevador.py) | `ELEVADOR_ANGULO_ARRIBA` | recuperador |

`calibrar-ruedas.py` tiene un `MODO`: `"recta"` (1 m), `"giro"` (360°) y
`"signo"` (+90°, para confirmar que el positivo gira a la **derecha** — de ahí
sale el signo de `OFFSET_Y`, ver [`../docs/setup-cancha.md`](../docs/setup-cancha.md)).

`diag-ultrasonido.py` no calibra nada: sirve cuando el sensor **lee cerca sin que
haya nada adelante**. Recorre fases (garra cerrada / abierta, elevador arriba /
abajo, quieto / en marcha) y compara las lecturas, para distinguir si el sensor
está viendo la garra abierta, si es el balanceo del arranque, o si ve una parte
fija del robot. Dejá el frente **libre** al correrlo.

El detalle de qué mirar en cada uno está en [`../docs/calibracion.md`](../docs/calibracion.md).

## Prueba de un solo hub

### `test-aproximacion.py` — acercarse y agarrar

Aísla el tramo más delicado de la misión, **sin canal, sin navegación y sin
cámara**: ponés el objeto en línea recta delante del recuperador y el robot
avanza, detecta, confirma quieto, remata por odometría, agarra, levanta, vuelve
al punto de partida y suelta.

Corrélo **antes** que las pruebas de dos hubs: si el agarre no anda, no tiene
sentido sumarle navegación y BLE encima. Y como el robot vuelve solo al punto de
partida, podés repetir moviendo únicamente el objeto.

Corrélo **una vez sin objeto** para conocer el ángulo de "garra cerrada en
vacío": comparando ese número con el de cada corrida sabés si agarró algo de
verdad o cerró en el aire.

### `test-acercamiento.py` — medir `OFFSET_OBJETO` (explorador, con teléfono)

Corre el acercamiento igual que la misión (buscar, centrar, acercarse hasta
`CY_CERCA`) y **se queda quieto** en el punto donde la misión fija la coordenada,
sin despejar ni transmitir. Es el único lugar donde `OFFSET_OBJETO` se puede
medir con sentido.

Necesita el teléfono conectado. Al frenar muestra `M`, imprime la pose y te
deja un minuto para medir con regla — **del medio del eje al centro del objeto**.
Mientras espera sigue imprimiendo la cámara, así verificás de paso el `cy` final.

## Pruebas de a dos hubs

Cada una son **dos programas**: el `-explorador` en el hub 1 y el
`-recuperador` en el hub 2. Encendé **siempre primero el recuperador** (queda
escuchando y muestra `R`).

### 1. Canal — `test-canal-*.py`

El explorador transmite una coordenada **fija** (300, 200, 0); el recuperador la
oye y maneja hacia ella. Sin cámara, sin garra, sin sensor. Si esto no anda, no
tiene sentido depurar nada más.

### 2. Ubicación — `test-ubicacion-*.py`

El explorador elige un sitio **al azar**, maneja hasta ahí, te da 3 s para
marcarlo y **poner el objeto real**, se corre de costado y transmite la
coordenada. El recuperador navega, hace la aproximación final con el
ultrasonido, agarra, vuelve y suelta.

Es la misión completa **menos la visión**: mismo `BLERadio`, mismo creep, misma
secuencia de garra que `recuperador/main.py`. Si esto cierra bien, lo único que
queda por depurar en la misión es la cámara.

> **Poné el objeto en la marca.** El recuperador ya no confirma con un par de
> lecturas: avanza lento buscando algo que ver. Sin objeto va a agotar
> `CREEP_MAX` y mostrar `X`.

## Sincronizar valores

Cuando termines de calibrar, los números van al `config.py` del robot **y**
a los archivos de esta carpeta que los repiten. Los que más se desincronizan:

| Valor | Vive en | Se repite en |
|-------|---------|--------------|
| `WHEEL_DIAMETER`, `AXLE_TRACK` | ambos `config.py` | los 4 `test-*` y `calibrar-ruedas.py` |
| `UMBRAL_DETECCION`, `DIST_OBJETIVO_FINAL`, `DIST_MIN_CONFIABLE` | `recuperador/config.py` | `test-ubicacion-recuperador.py`, `calibrar-ultrasonido.py` |
| `MARGEN_APROXIMACION`, `VEL_APROXIMACION`, `CREEP_MAX` | `recuperador/config.py` | `test-ubicacion-recuperador.py` |
| `OFFSET_X`, `OFFSET_Y` | `recuperador/config.py` | `test-ubicacion-recuperador.py` |
| `GARRA_*`, `ELEVADOR_*` | `recuperador/config.py` | `test-ubicacion-recuperador.py`, `calibrar-garra.py`, `calibrar-elevador.py` |
