# Setup de cancha

Cómo colocar los dos robots para que las coordenadas signifiquen lo mismo, y en
qué orden encenderlos.

## El origen compartido

Las coordenadas que transmite el explorador se miden **desde el punto donde
arranca**. Para que el recuperador entienda esas coordenadas, tiene que arrancar
en el **mismo punto** y mirando en la **misma dirección**.

```
        +Y (costado)
         │
         │      • objeto (obj_x, obj_y)
         │
  origen ●───────────▶ +X (adelante, rumbo 0°)
      (0,0)
   los DOS robots
   arrancan acá
```

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
**Recuperador:** `R` escuchando → (beep al recibir) → navega → `G` agarra (baja,
cierra, levanta) → vuelve → `A` suelta → `F` fin. Si al llegar el ultrasonido no
confirma el objeto: `X` + beep grave (no agarra).
