# Contrato de datos

Qué se manda entre los tres protagonistas y en qué formato. Si cambiás uno de
estos formatos, tenés que cambiarlo en los **dos** lados a la vez.

```
📱 Teléfono  ──AppData (Web BLE)──▶  🤖 Explorador  ──broadcast/observe──▶  🦾 Recuperador
```

## 1. Teléfono → Explorador (AppData)

El teléfono (página Teachable Machine) manda **5 bytes** en el modo 0.
En el explorador se leen con `app.get_bytes(mode=0)`.

```python
app = AppData([(0, 5)])
clase, confianza, cx, area, cy = app.get_bytes(mode=0)
```

| byte | dato | rango | significado |
|------|------|-------|-------------|
| 0 | `clase` | 0–255 | índice de la categoría del modelo (0 = primera clase) |
| 1 | `confianza` | 0–100 | % de certeza de la predicción |
| 2 | `cx` | 0–100 | centro horizontal del objeto, % desde la izquierda (**50 = centrado**) |
| 3 | `area` | 0–100 | tamaño relativo del objeto |
| 4 | `cy` | 0–100 | altura del borde **inferior** del objeto (**0 = arriba/lejos, 100 = abajo/encima**) |

> Teachable Machine dice **qué** objeto es (clase + confianza). El **dónde**
> (`cx`, `cy`, `area`) lo calcula la página a partir del blob de color del objeto.

### Por qué `cy` y no `area`

El teléfono va **inclinado hacia abajo**, no mirando al horizonte. Con eso, un
objeto apoyado en el piso **baja en el cuadro de forma monótona** a medida que el
robot se acerca, así que `cy` es un proxy de distancia confiable: no lo afecta la
luz ni cuánto fondo del mismo tono haya en el cuadro. El `area` sí, y por eso el
explorador ya no la usa como criterio de frenado (solo como filtro de ruido).

`cy` es el **borde inferior** del blob, no su centro: ese es el punto donde el
objeto toca el piso, que es lo que se relaciona con la distancia. Se toma la fila
más baja con al menos 2 píxeles del tono, para no engancharse con un píxel suelto.

Los dos números se calculan sobre el **recorte cuadrado central** del video — el
mismo encuadre que se ve en pantalla. Si cambiás la inclinación o la altura del
teléfono, hay que recalibrar `CX_CENTRO` y `CY_CERCA` en `explorador/config.py`.

## 2. Explorador → Recuperador (broadcast BLE)

El explorador transmite una tupla de enteros por el canal BLE. El recuperador la
recibe con `hub.ble.observe(CANAL)` (devuelve `None` si no oye nada).

```python
# explorador
hub.ble.broadcast((obj_x, obj_y, clase))

# recuperador
objetivo = hub.ble.observe(CANAL)   # None o (obj_x, obj_y, clase)
```

| campo | unidad | significado |
|-------|--------|-------------|
| `obj_x` | mm | posición del objeto en el eje X (adelante) desde el origen |
| `obj_y` | mm | posición del objeto en el eje Y (costado) desde el origen |
| `clase` | 0–255 | qué objeto es (por si hay más de uno) |

- **Canal:** el mismo número (`CANAL`) en los dos `config.py`. Por defecto **1**.
- **Límite:** el payload de broadcast es de 26 bytes; tres enteros entran holgados.

## 3. Marco de coordenadas compartido

Las coordenadas `(obj_x, obj_y)` solo significan lo mismo para los dos robots si
**ambos arrancan en el mismo lugar y mirando en la misma dirección**:

- Origen `(0, 0)` = punto de partida común.
- Rumbo `0°` = hacia adelante (eje +X). **El eje +Y es hacia la DERECHA física**,
  porque `turn()` positivo gira en sentido horario (convención de Pybricks) y el
  explorador integra su pose con ese mismo rumbo. Un punto a la izquierda tiene
  `y` **negativo**. Ver [`setup-cancha.md`](setup-cancha.md).
- Cada robot hace `robot.reset()` al empezar, así su odometría cuenta desde el origen.

Si los robots no arrancan alineados, el recuperador irá a un punto equivocado
aunque el explorador haya calculado bien. Ver [`setup-cancha.md`](setup-cancha.md).
