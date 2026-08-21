# Setup de cancha

Cómo colocar los dos robots para que las coordenadas signifiquen lo mismo, y en
qué orden encenderlos.

## El origen compartido

Las coordenadas que transmite el explorador se miden **desde el punto donde
arranca**. Para que el recuperador entienda esas coordenadas, tiene que arrancar
en el **mismo punto** y mirando en la **misma dirección**.

```
   visto DESDE ARRIBA

  origen ●───────────▶ +X (adelante, rumbo 0°)
      (0,0)  │
             │      • objeto (obj_x, obj_y)
             │
             ▼ +Y (la DERECHA física del robot)
```

### ⚠️ El signo de `+Y`: es la DERECHA, no la izquierda

`turn()` positivo gira **a la derecha** (horario) — es la convención estándar de
Pybricks. El explorador integra su pose con `y += paso * sin(rumbo)` usando ese
mismo rumbo (`explorador/main.py:67-68`), así que **`+y` es la derecha física**.

Esto se verificó tres veces (2026-08-20): con el ensayo `MODO = "signo"` de
[`../pruebas/calibrar-ruedas.py`](../pruebas/calibrar-ruedas.py), con el centrado
del explorador (`error = cx - CX_CENTRO` con `>0 = objeto a la derecha` alimenta
un giro positivo, y centra bien), y con la fórmula de la pose.

**Consecuencia práctica:** un robot que arranca a la **izquierda** del explorador
está en `y` **negativo**. El recuperador arranca 165 mm a la izquierda, así que
`OFFSET_Y = -165`.

> La navegación nunca estuvo mal: los dos robots usan la misma convención, así
> que son consistentes entre sí. Lo que estaba mal era la descripción en los
> comentarios ("izquierda = +y"), y de ahí salía un `OFFSET_Y` con el signo
> invertido — 33 cm de error lateral, más de lo que el ultrasonido perdona.

### Cómo alinearlos
1. Marcá en la cancha el **punto de origen** (una cruz de cinta) y una **línea de
   rumbo** que salga de ahí (hacia dónde es "adelante", el eje +X).
2. Colocá el explorador con su centro sobre la cruz y su frente sobre la línea.
3. Corré la misión del explorador (o su viaje). Cuando termine, retiralo.
4. Colocá el recuperador **en la misma cruz, sobre la misma línea**, mirando igual.
5. Corré la misión del recuperador.

> Si tenés dos cruces (no podés reusar la misma), asegurate de que estén en el
> mismo lugar físico o que sepas el offset entre ellas. El error de alineación se
> traslada directo al punto al que va el recuperador.

### El punto de referencia: el MEDIO DEL EJE

Todas las distancias del sistema —el origen de cada robot, `OFFSET_X` /
`OFFSET_Y`, y también `OFFSET_OBJETO` en el explorador— se miden desde el
**punto medio entre las dos ruedas**, proyectado en el piso.

No es el centro geométrico del chasis ni el paragolpes delantero. `DriveBase`
modela un diferencial: el robot pivota alrededor del medio del eje, y toda la
odometría (`robot.distance()`, `robot.angle()`, y la pose `(x, y)` que integra
el explorador) está referida a ese punto. Si medís desde otro lado, el error se
suma directo a la coordenada.

**Cómo marcarlo:** mirando desde arriba, ubicá los dos puntos de contacto de las
ruedas con el piso; el medio del segmento que los une es el punto. Pegá una
cinta en el chasis justo encima para tenerlo a mano.

**Para medir el offset entre los dos robots:** ponelos en sus posiciones reales,
ambos alineados con la línea de rumbo, y medí entre las dos marcas las **dos
componentes por separado** — la perpendicular al avance es `OFFSET_Y`, la
paralela es `OFFSET_X`. No midas la diagonal.

## Canal BLE

Los dos robots hablan por el mismo **canal**. Está en el `config.py` de cada uno
como `CANAL` (por defecto **1**). Si corren dos equipos cerca, cambiá el número
en ambos a la vez para no cruzar señales.

## Orden de arranque

1. **Recuperador primero.** Al arrancar queda escuchando (`observe`) y mostrando
   `R` en la pantalla. Puede esperar tranquilo.
2. **Teléfono → Explorador.** Abrí la página de detección, conectá el hub del
   explorador y verificá que llegan los datos de la cámara.
3. **Explorador después.** Busca, centra, se acerca y **transmite** la coordenada
   (~5 s repetida). El recuperador la oye, hace `beep` y arranca.

### Qué muestra cada pantalla (para seguir la misión)

**Explorador:** `B` busca → `C` centra → `A` se acerca → `T` transmite → `F` fin.

> Entre `A` y `T` el explorador **se corre de costado** (retrocede un poco, gira 90° y
> sale perpendicular). No es un error: si retrocediera en línea quedaría sobre el camino
> del recuperador, y el ultrasonido del recuperador lo vería a **él** en vez del objeto.
> Si el costado al que sale está bloqueado en tu cancha, invertí el signo de
> `GIRO_DESPEJE` en `explorador/config.py`.

**Recuperador:** `R` escuchando → (beep al recibir) → navega → `G` agarra (baja,
cierra, levanta) → vuelve → `A` suelta → `F` fin. Si al llegar el ultrasonido no
confirma el objeto: `X` + beep grave (no agarra).
