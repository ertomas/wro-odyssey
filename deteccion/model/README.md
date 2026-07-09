# Modelo de Teachable Machine (incluido)

Acá van los archivos del modelo entrenado. La página `deteccion/index.html` los carga
**sola al abrir** (no hay que pegar ningún link).

## Qué archivos van acá

Del export TensorFlow.js de Teachable Machine:

- `model.json` — arquitectura + referencia a los pesos (`weightsManifest`).
- `metadata.json` — nombres de las clases (labels).
- `weights.bin` — los pesos del modelo.

## Cómo regenerarlos / cambiar el modelo

1. Entrená el modelo en [teachablemachine.withgoogle.com](https://teachablemachine.withgoogle.com)
   (modo **Imagen**) con fotos de tu objeto.
2. **Export Model** → pestaña **Tensorflow.js** → **Download my model**.
3. Descomprimí el `.zip` y copiá `model.json`, `metadata.json` y `weights.bin` **acá**
   (reemplazando los que estén).

> El orden de las clases define el índice `clase` que se le manda al hub. Ajustá
> `CLASES_OBJETIVO` en `explorador/config.py` para que apunte al/los objeto(s)
> correcto(s) — es una lista, así que puede ser una sola clase o varias.
