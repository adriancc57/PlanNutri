# Plan de Alimentación -- Visor Web

Este proyecto permite visualizar un **plan de alimentación semanal** de
forma sencilla desde un teléfono o navegador web, con **letra grande y
navegación simple**.

Fue diseñado especialmente para facilitar la lectura del plan a personas
que tienen dificultad para leer PDFs con texto pequeño.

El sistema permite:

-   Consultar las comidas por **día de la semana**
-   Seleccionar el **tipo de comida** (Desayuno, Colación, Comida, etc.)
-   Mostrar el contenido con **letras grandes**
-   Abrir el **PDF original del plan** en otra pestaña si se desea ver
    el documento completo

El sitio funciona completamente en **modo estático**, por lo que puede
desplegarse fácilmente en **GitHub Pages** o cualquier servidor web.

------------------------------------------------------------------------

# Estructura del proyecto

    project/
    │
    ├── index.html        # Página principal del visor
    ├── ver-pdf.html      # Visor del PDF dentro del navegador
    ├── plan.json         # Plan de alimentación en formato JSON
    ├── plan.pdf          # PDF original del nutriólogo
    └── README.md

------------------------------------------------------------------------

# Formato del JSON

El archivo `plan.json` contiene el plan estructurado por **día y tipo de
comida**.

Ejemplo:

``` json
{
  "Lunes": {
    "Desayuno": "Smoothie...",
    "Colación 1": "Huevos con vegetales...",
    "Comida": "Caldo de setas...",
    "Colación 2": "Manzana 1 pieza",
    "Cena": "Carlota de fresa..."
  }
}
```

La página web utiliza esta estructura para mostrar la comida
seleccionada.

------------------------------------------------------------------------

# Cómo usar el visor

1.  Abrir `index.html` en un navegador\
2.  Seleccionar:
    -   Día de la semana
    -   Tipo de comida\
3.  El contenido aparecerá automáticamente en pantalla

También existe un botón para:

**Ver plan completo en PDF**

Esto abrirá el archivo `plan.pdf` en otra pestaña dentro del navegador.

------------------------------------------------------------------------

# Actualizar el plan de alimentación

Cuando el nutriólogo envíe un nuevo plan:

1.  Reemplazar el archivo:

```{=html}
<!-- -->
```
    plan.pdf

2.  Generar el nuevo JSON con el contenido del plan.

3.  Reemplazar el archivo:

```{=html}
<!-- -->
```
    plan.json

4.  Subir los cambios al repositorio o servidor.

El visor mostrará automáticamente la nueva información.

------------------------------------------------------------------------

# Tecnologías utilizadas

-   HTML
-   CSS
-   JavaScript
-   JSON

No se requiere backend ni base de datos.

------------------------------------------------------------------------

# Despliegue recomendado

El proyecto puede desplegarse fácilmente en:

-   **GitHub Pages**
-   **Netlify**
-   **Cualquier servidor web estático**

------------------------------------------------------------------------

# Objetivo del proyecto

El objetivo es crear una forma **simple y accesible** de consultar un
plan de alimentación desde el teléfono, evitando la dificultad de leer
documentos PDF con texto pequeño.
