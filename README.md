# Plan de Alimentación -- Visor Web

https://adriancc57.github.io/PlanNutri/

Este proyecto permite consultar planes de alimentación semanales por persona desde un navegador o teléfono. Funciona como una aplicación estática, sin backend ni dependencias.

## Selector de persona

La página principal permite seleccionar:

- `angelica` — Angelica
- `adrian` — Adrian
- `karina` — Karina

Al cambiar de persona se actualizan el título, el plan, las recomendaciones especiales y el enlace al PDF correspondiente.

## Estructura multi-persona

`plan.json` mantiene un objeto por persona y una lista global de ingredientes:

```json
{
  "angelica": {
    "recomendacionesespeciales": {},
    "plan": {}
  },
  "adrian": {
    "recomendacionesespeciales": {},
    "plan": {}
  },
  "karina": {
    "recomendacionesespeciales": {},
    "plan": {}
  },
  "ingredientes": []
}
```

El plan existente pertenece solamente a `angelica`. Los planes de `adrian` y `karina` permanecen vacíos hasta que existan datos propios; no se replica ni se inventa contenido.

## Ingredientes globales

La lista procede siempre de `data.ingredientes` y es compartida por todas las personas. El estado de sus checkboxes se conserva globalmente en `localStorage["ingredientes-checked"]`; cambiar de persona no borra ni separa la lista.

## PDFs por persona

El botón abre `ver-pdf.html?persona=<persona>` en otra pestaña. El visor usa un mapa explícito para resolver:

- `angelica` → `angelica.pdf`
- `adrian` → `adrian.pdf`
- `karina` → `karina.pdf`

Si el parámetro no es válido, se utiliza Angelica como persona predeterminada.

## Uso

1. Servir el directorio con cualquier servidor web estático.
2. Abrir `index.html`.
3. Elegir persona, día y comida.
4. Consultar recomendaciones especiales cuando existan o abrir el PDF individual.

## Pruebas en local

Debido a que la aplicación carga `plan.json` mediante `fetch()`, no debe abrirse
`index.html` directamente desde Finder usando `file://`, ya que el navegador
bloqueará la carga del JSON por CORS.

Para ejecutar el proyecto localmente, abrir una terminal en la raíz del proyecto
y ejecutar:

```bash
python3 -m http.server 8000