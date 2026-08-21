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

> ⚠️ **No lo midas con regla y lo des por terminado.** Nominalmente es la
> separación entre las ruedas, pero funciona como una **perilla de calibración**,
> no como una medida. Al pivotar, los neumáticos restriegan de costado: ese
> patinaje hace que el robot rote **menos** de lo que la geometría predice, y se
> compensa declarando un track **más grande que el real**. Sumale que el punto de
> contacto efectivo de un neumático ancho no está en su centro geométrico.
> Resultado: **el valor calibrado casi siempre es mayor que el medido** (en el
> recuperador, 161 mm medidos → ~165 calibrados). Medí con regla para tener un
> punto de partida, y después **confiá en el comportamiento, no en la regla**.

`DriveBase` calcula cuánto rotar las ruedas a partir del `AXLE_TRACK` que le
declarás. Si le decís que están **más separadas** de lo que están, calcula un
arco más largo y el robot **rota de más**:

```
giro_real = giro_pedido × (AXLE_TRACK declarado / separación real)
```

O sea: **subir `AXLE_TRACK` → gira MÁS. Bajarlo → gira MENOS.**

1. Calibrá `WHEEL_DIAMETER` **primero**: el giro se apoya en él.
2. Pedí **varias vueltas** (`robot.turn(1080)` = 3 vueltas), no una sola. El error
   de una vuelta suele ser demasiado chico para medirlo a ojo; con 3 se
   triplica y lo ves claro. Marcá el frente del robot con una línea en el piso.
3. Estimá cuántos grados giró **de verdad** en total (ej.: le faltó media vuelta
   de 1080 → giró 900).
4. Ajustá:  `nuevo = actual × (grados_pedidos / grados_reales)`
   - Giró de **menos** → **subí** `AXLE_TRACK`.
   - Giró de **más** → **bajalo**.
5. Repetí hasta que vuelva a la línea.

> Este número importa más que el diámetro: el error de giro es **angular** y se
> abre con la distancia. 2° de error son ~35 mm de desvío lateral a un metro, y
> el desvío lateral es el que la misión no perdona (el ultrasonido corrige de
> más o de menos, pero si el robot pasa de costado al objeto no lo ve nunca).

> Valores de arranque en los `config.py`: `WHEEL_DIAMETER = 56`, `AXLE_TRACK = 112`.
> Son un punto de partida típico de SPIKE Prime; **hay que calibrarlos igual**.

### Valores actuales por robot (completar cuando calibren)

| Robot | WHEEL_DIAMETER | AXLE_TRACK | Fecha |
|-------|----------------|------------|-------|
| Explorador | 56 | 113 | 2026-07-04 |
| Recuperador | 56 | 164 | 2026-08-20 |

> Recuperador (2026-08-20): recta 800 mm pedidos → 798 reales, dentro de
> tolerancia, `WHEEL_DIAMETER` sin cambios. `AXLE_TRACK` por ensayo de 3 vueltas:
> 164 (la regla da 161 — ver la advertencia de arriba). Calibrado en piso duro,
> **no** en la lona de competencia: verificar con una corrida cuando esté la pista.

## Inclinación del teléfono (explorador)

**El teléfono va inclinado hacia abajo, no vertical.** Vertical mira al horizonte y el
objeto se escapa por el borde inferior del cuadro justo cuando el robot está más cerca
— que es exactamente donde tiene que fijar la coordenada. Además, el robot lo embiste.

**Cómo elegir el ángulo:** el criterio no es un número de grados, es que el suelo
visible **llegue más allá del borde lejano de la pista**, sin gastar cuadro en lo que
hay más allá. Como la pista no es grande, con poca inclinación alcanza.

**En este robot son ~15°**, que es lo máximo que permite la construcción, y es
suficiente: corta el horizonte dentro de la pista. No hace falta más.

```
    ANTES (vertical)              DESPUES (~25 grados)
                                
    [tel]|        objeto          [tel]\
         |                              \
         |                               v   objeto
    -----+---------[#]---         --------[#]------------
    se escapa por abajo           sigue en cuadro hasta el final
```

> Cada vez que cambien la inclinación o la altura del montaje hay que **recalibrar
> `CX_CENTRO`, `CY_CERCA` y `OFFSET_OBJETO`**. Son los tres números que dependen de
> la geometría de la cámara.

## Acercamiento del explorador: `CY_CERCA` y sus guardas

Solo en el explorador. El paso `A` se acerca al objeto y ahí fija la coordenada que
transmite, así que **de qué tan cerca la fije depende toda la misión**: el resto del
sistema hereda ese error.

El criterio de frenado es `cy` (qué tan abajo está el objeto en el cuadro), no el
`area`. El `area` cuenta *todos* los píxeles del tono, incluido el fondo, así que sube
y baja con la luz; `cy` con la cámara inclinada baja de forma monótona al acercarse.

- **`CY_CERCA`** (0–100, actual 80): el `cy` al que frena. **Cómo calibrarlo:** poné el
  objeto a la distancia a la que querés que frene, mirá el número **«altura Y»** en la
  pantalla del teléfono y ese valor va acá. Subilo para que se acerque más.
- **`OFFSET_OBJETO`** (mm, actual 150): cuánto hay entre el robot y el objeto cuando
  frena. Medilo con regla **después** de fijar `CY_CERCA`. Ahora que el frenado es
  repetible, este número por fin se puede medir una vez y queda bien.
  > **Medilo desde el MEDIO DEL EJE**, no desde el paragolpes delantero. Toda la
  > odometría está referida a ese punto (ver [`setup-cancha.md`](setup-cancha.md)).
  > Medir desde el frente te deja la coordenada corta por el voladizo del chasis
  > —fácilmente 5-8 cm— y ese error se traslada tal cual al recuperador.

> **Con poca inclinación (15°), `cy` sube más despacio con la distancia.** Un mismo
> `CY_CERCA` frena **más lejos** que con la cámara más inclinada, así que el `150` de
> `OFFSET_OBJETO` casi seguro se queda corto: mídanlo, no lo asuman. Y como el rango
> útil de `cy` se comprime, conviene tomar los valores de la pantalla en vez de
> estimarlos — la relación `cy`↔distancia no es lineal.
- **`CY_PERDIDA_CERCA`** (0–100, actual 70): si pierde el objeto habiendo llegado a este
  `cy`, asume que se fue por el borde inferior porque lo tiene encima, y da el
  acercamiento por terminado. Tiene que ser **menor** que `CY_CERCA`. Bajalo si el
  explorador sale a buscar de nuevo cuando en realidad ya había llegado.
- **`AREA_MIN_VALIDO`** (0–100, actual 2): área mínima para creerle al blob. Filtra
  manchas de ruido del mismo tono. Subilo si el explorador reacciona a reflejos.
- **`AVANCE_MIN_ACERCAMIENTO`** (mm, actual 200): cuánto tiene que avanzar como mínimo
  antes de aceptar "ya estoy cerca". Subilo si fija la coordenada demasiado lejos.
- **`CONFIRMACIONES_CERCA`** (actual 3): lecturas seguidas con `cy >= CY_CERCA` antes
  de frenar. Filtra los picos de un cuadro suelto.
- **`PERDIDAS_MAX`** (actual 10): lecturas seguidas sin ver el objeto antes de decidir
  qué hacer. A 20 ms por lectura, 10 ≈ 0.2 s. **El robot frena en la primera pérdida**,
  siempre: perder el objeto es justamente lo que pasa cuando lo tenés encima.
- **`ACERCAMIENTO_MAX`** (mm, actual 1500) y **`ACERCAMIENTO_TIMEOUT`** (ms, actual
  25000): topes de seguridad. Si el explorador corta siempre por acá en vez de por
  confirmación, es que `CY_CERCA` está demasiado alto y nunca se alcanza.

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

## Ultrasonido y aproximación final: `DIST_AGARRE` y compañía

Solo en el recuperador (Port.E), montado a **~7 cm del punto de agarre**. Para no
embestir el objeto, el robot **no maneja a ciegas** hasta la coordenada: frena un
margen antes y hace el último tramo **despacio mirando el sensor**, deteniéndose
apenas el objeto entra en rango.

- **`DIST_AGARRE`** (mm, actual 60): lectura esperada con el objeto en la garra.
  Poné el objeto agarrado y mirá qué lee el sensor (aparece en la terminal como
  `Ultrasonido: … mm`); ese número va acá.
- **`TOLERANCIA_AGARRE`** (mm, actual 20): frena cuando `d <= DIST_AGARRE + esto`.
  Subilo si frena demasiado lejos; bajalo si igual lo toca antes de frenar.
- **`MARGEN_APROXIMACION`** (mm, actual 300): cuánto antes de la coordenada deja de
  ir rápido y arranca la aproximación lenta. Subilo si la coordenada de la cámara
  es imprecisa (frena antes y se acerca más lento pero más seguro). Tiene que ser
  **más grande que el error radial del explorador**: si el explorador sobreestima la
  distancia y este margen es chico, el robot embiste el objeto a velocidad de
  crucero antes de empezar a mirar el sensor.
- **`VEL_APROXIMACION`** (mm/s, actual 40): velocidad del tramo final. Más lento =
  frena más justo, menos chance de pasarse.
- **`CREEP_MAX`** (mm, actual 550): cuánto avanza lento como máximo buscando el
  objeto. Si no lo detecta en esa distancia, se rinde (muestra `X`) en vez de
  seguir de largo.

> Con estos tres valores el tramo lento cubre la ventana `[dist-300, dist+250]`
> alrededor de la coordenada recibida, y en el peor caso tarda `550 / 40 ≈ 14 s`.
> Si el reloj de la misión aprieta, lo primero a recortar es `CREEP_MAX`.
