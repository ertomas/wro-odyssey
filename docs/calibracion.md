# Calibración

Cada robot es distinto. Estos números viven en el `config.py` de cada carpeta y
hay que medirlos una vez (y volver a medir si cambiás ruedas o el chasis).

## Ruedas: `WHEEL_DIAMETER` y `AXLE_TRACK`

Estos dos números hacen que `robot.straight(mm)` y `robot.turn(grados)` sean
precisos. Si el robot avanza de más/menos o gira de más/menos, están mal.

### `WHEEL_DIAMETER` (diámetro de la rueda, en mm)
1. Poné `robot.straight(1000)` (1 metro) en un programa de prueba.
2. Medí con una regla cuánto avanzó **de verdad**.
3. Ajustá: `nuevo = actual × (1000 / lo_que_avanzó_en_mm)`.
   - Avanzó de más → bajá el diámetro. Avanzó de menos → subilo.

También podés medir el diámetro directo con una regla, pero calibrar con 1 m es
más preciso porque promedia el error.

### `AXLE_TRACK` (distancia entre ruedas, en mm)
1. Poné `robot.turn(360)` (una vuelta completa).
2. Si giró de más, **subí** `AXLE_TRACK`; si giró de menos, **bajalo**.
3. Repetí hasta que 360° sea una vuelta exacta.

> Valores de arranque en los `config.py`: `WHEEL_DIAMETER = 56`, `AXLE_TRACK = 112`.
> Son un punto de partida típico de SPIKE Prime; **hay que calibrarlos igual**.

### Valores actuales por robot (completar cuando calibren)

| Robot | WHEEL_DIAMETER | AXLE_TRACK | Fecha |
|-------|----------------|------------|-------|
| Explorador | 56 | 113 | 2026-07-04 |
| Recuperador | 56 | 160 | 2026-07-04 |

## Garra: `GARRA_DUTY_LIMIT`, `GARRA_VELOCIDAD` y `GARRA_DUTY_SOSTEN`

Solo en el recuperador (Port.C). La garra cierra con
`garra.run_until_stalled(-GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)`:
gira hasta que encuentra resistencia (el objeto) y ahí se frena.

> En **este** robot la pinza **abre con velocidad + y cierra con velocidad -**
> (al revés de lo típico). `main.py` ya usa los signos correctos.

- **`GARRA_DUTY_LIMIT`** (% de fuerza durante el cierre, actual 90):
  - Si **no agarra** bien el objeto o se resbala → subilo (aprieta más fuerte).
  - Si **aplasta** el objeto o fuerza el motor → bajalo.
- **`GARRA_VELOCIDAD`** (deg/s, actual 300): qué tan rápido abre/cierra. Más lento
  es más suave pero más lento; rara vez hay que tocarlo.
- **`GARRA_DUTY_SOSTEN`** (% de fuerza continua, actual 100): después de cerrar,
  `run_until_stalled` deja el motor en *coast* (fuerza cero) y el objeto se cae.
  Por eso se mantiene el apriete con `garra.dc(-GARRA_DUTY_SOSTEN)` mientras carga.
  Bajalo si fuerza mucho el motor; subilo si el objeto se escapa al moverse.

> Tip: probá la garra con el objeto real. Un vaso de plástico y una pieza de LEGO
> necesitan fuerzas distintas.

## Elevador: `ELEVADOR_ANGULO_ARRIBA` y `ELEVADOR_VELOCIDAD`

Solo en el recuperador (Port.D). Sube/baja la garra. **No tiene tope arriba**:
en reposo queda ABAJO y esa posición al arrancar es el cero. La garra arranca y
termina abajo; sube sólo después de agarrar el objeto.

- **`ELEVADOR_ANGULO_ARRIBA`** (grados desde abajo hasta levantada, actual -90):
  cuánto sube tras agarrar. Si **baja** en vez de subir, invertí el signo. Ajustá
  la magnitud para que levante el objeto lo justo sin forzar.
- **`ELEVADOR_VELOCIDAD`** (deg/s, actual 100): qué tan rápido sube/baja.

> Antes de subir el programa, dejá la garra en su **reposo abajo**: ahí queda el
> cero. Si el elevador se traba al arrancar, casi siempre es el **signo** del
> ángulo (está empujando contra el tope).

## Ultrasonido: `DIST_AGARRE` y compañía

Solo en el recuperador (Port.E), montado a **~7 cm del punto de agarre**. Al llegar
al objetivo confirma que el objeto quedó al alcance y corrige el avance final.

- **`DIST_AGARRE`** (mm, actual 60): lectura esperada con el objeto en la garra.
  Poné el objeto agarrado y mirá qué lee el sensor (aparece en la terminal como
  `Ultrasonido N: … mm`); ese número va acá.
- **`TOLERANCIA_AGARRE`** (mm, actual 15): margen para dar por bueno el rango.
- **`DIST_SIN_OBJETO`** (mm, actual 250): más lejos que esto = "no hay objeto".
- **`PASO_CORRECCION`** (mm, actual 20) e **`INTENTOS_AGARRE`** (actual 5): cuánto
  avanza por intento y cuántas veces reintenta acercarse antes de rendirse.
