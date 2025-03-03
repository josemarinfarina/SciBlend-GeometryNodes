# SciBlend-GeometryNodes

Un addon para Blender que permite importar y aplicar mapas nodales de Geometry Nodes desde archivos JSON.

## Características

- Importación de mapas nodales desde archivos JSON
- Transformaciones predefinidas (traslación, rotación, escala, espejo, array)
- Interfaz sencilla e intuitiva

## Instalación

1. Descarga el archivo ZIP del addon
2. En Blender, ve a Edit > Preferences > Add-ons
3. Haz clic en "Install..." y selecciona el archivo ZIP descargado
4. Activa el addon marcando la casilla

## Uso

1. En el panel lateral del área 3D (tecla N), encontrarás la pestaña "SciBlend"
2. Para importar un mapa nodal personalizado, haz clic en "Seleccionar JSON" y elige un archivo JSON
3. Para aplicar una transformación predefinida, selecciona un objeto y haz clic en el botón correspondiente

## Formato JSON

Los archivos JSON deben seguir una estructura específica. Puedes encontrar ejemplos en la carpeta `json_templates`.

Estructura básica:

```json
{
    "name": "Nombre del mapa nodal",
    "description": "Descripción",
    "nodes": [
        {
            "id": "identificador_unico",
            "type": "TipoDeNodo",
            "location": [x, y],
            "inputs": {
                "NombreInput1": valor,
                "NombreInput2": valor
            }
        }
    ],
    "links": [
        {
            "from_node": "id_nodo_origen",
            "from_socket": "socket_origen",
            "to_node": "id_nodo_destino",
            "to_socket": "socket_destino"
        }
    ],
    "inputs": [
        {
            "name": "Nombre",
            "type": "TipoSocket"
        }
    ],
    "outputs": [
        {
            "name": "Nombre",
            "type": "TipoSocket"
        }
    ]
}
```

## Transformaciones predefinidas

- **Traslación**: Mueve el objeto en el eje X
- **Rotación**: Rota el objeto 45 grados en el eje Z
- **Escala**: Escala el objeto al doble de su tamaño
- **Espejo**: Crea un espejo del objeto en el eje X
- **Array**: Crea un array lineal de 5 instancias del objeto

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. 