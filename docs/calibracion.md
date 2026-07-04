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
| Explorador | 56 (sin calibrar) | 112 (sin calibrar) | — |
| Recuperador | 56 (sin calibrar) | 112 (sin calibrar) | — |

## Garra: `GARRA_DUTY_LIMIT` y `GARRA_VELOCIDAD`

Solo en el recuperador. La garra cierra con
`garra.run_until_stalled(GARRA_VELOCIDAD, duty_limit=GARRA_DUTY_LIMIT)`:
gira hasta que encuentra resistencia (el objeto) y ahí se frena.

- **`GARRA_DUTY_LIMIT`** (% de fuerza, arranca en 50):
  - Si **no agarra** bien el objeto o se resbala → subilo (aprieta más fuerte).
  - Si **aplasta** el objeto o fuerza el motor → bajalo.
- **`GARRA_VELOCIDAD`** (deg/s, arranca en 300): qué tan rápido cierra. Más lento
  es más suave pero más lento; rara vez hay que tocarlo.

> Tip: probá la garra con el objeto real. Un vaso de plástico y una pieza de LEGO
> necesitan fuerzas distintas.
