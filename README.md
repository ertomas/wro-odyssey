# 🤖 WRO Odyssey — Misión cámara: dos robots

Código final de competencia (WRO 2025) para la misión de la cámara.
Equipo: **Tomas · Gael · Juan Marcos**.

Un **robot explorador** usa el teléfono como cámara con IA (Teachable Machine),
reconoce un objeto y calcula su posición. Le transmite esa posición por Bluetooth
a un **robot recuperador**, que navega hasta el objeto y lo agarra con una garra.

```
📱 Teléfono          🤖 Explorador              🦾 Recuperador
(cámara + IA)  ──▶   (busca, centra,   ──▶      (navega hasta el
                      ubica el objeto)   BLE      objeto y lo agarra)
   AppData                            broadcast/observe
[clase,conf,cx,area]                   (obj_x, obj_y, clase)
```

## Los dos robots

| Robot | Carpeta | Hub | Rol |
|-------|---------|-----|-----|
| Explorador | [`explorador/`](explorador/) | Hub 1 | Cámara + IA: busca, centra y ubica el objeto; transmite la coordenada |
| Recuperador | [`recuperador/`](recuperador/) | Hub 2 | Escucha la coordenada, navega hasta el objeto y lo agarra con la garra |

## Puertos (por defecto — ajustar en cada `config.py`)

| Puerto | Explorador | Recuperador |
|--------|------------|-------------|
| A | Motor izquierdo | Motor izquierdo |
| B | Motor derecho | Motor derecho |
| C | — | Garra |

## Cómo correr la misión

1. **Calibrar** cada robot (ruedas y garra) — ver [`docs/calibracion.md`](docs/calibracion.md).
2. **Subir el código** con [Pybricks Code](https://code.pybricks.com):
   - Abrí la carpeta `explorador/` como proyecto y corré `main.py` en el **hub 1**.
   - Abrí la carpeta `recuperador/` como proyecto y corré `main.py` en el **hub 2**.
   - Cada carpeta es un proyecto multi-archivo: `main.py` importa a `config.py`, así que
     los dos archivos tienen que estar en el mismo proyecto.
3. **Colocar los dos robots** en el mismo origen y mirando en la misma dirección —
   ver [`docs/setup-cancha.md`](docs/setup-cancha.md).
4. **Encender primero el recuperador** (queda escuchando) y después el explorador.
5. **Abrir la página de detección** en el teléfono y conectarla al explorador:
   [`deteccion/index.html`](deteccion/index.html). Es una página HTML suelta (sin build):
   servila por `https://` o `localhost` (Web Bluetooth y la cámara no andan con `file://`).
   Desde la laptop, lo más rápido: `cd deteccion && python -m http.server` y abrila desde el
   teléfono con la IP de la laptop, o subila a cualquier hosting estático.

## Antes de tocar código: probá el canal

Si la comunicación entre los dos hubs anda, el resto es más fácil de depurar.
Corré los dos programas de [`pruebas/`](pruebas/) (uno en cada hub) para confirmar
`broadcast`/`observe` con una coordenada fija, sin cámara.

## Documentación

- [`deteccion/index.html`](deteccion/index.html) — página de la cámara con Teachable Machine (HTML suelto).
- [`docs/contrato-datos.md`](docs/contrato-datos.md) — qué datos se mandan y en qué formato.
- [`docs/calibracion.md`](docs/calibracion.md) — medir las ruedas y ajustar la garra.
- [`docs/setup-cancha.md`](docs/setup-cancha.md) — origen, rumbo y orden de arranque.
