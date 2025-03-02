bl_info = {
    "name": "SciBlend-GeometryNodes",
    "author": "Tu Nombre",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > SciBlend",
    "description": "Importa mapas nodales de Geometry Nodes desde archivos JSON",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy
from bpy.props import StringProperty, PointerProperty, BoolProperty
from bpy.types import PropertyGroup

# Importar módulos
from . import operators
from . import ui

# Propiedades globales del addon
class SciBlendGeometryNodesProperties(PropertyGroup):
    json_filepath: StringProperty(
        name="Ruta del JSON",
        description="Ruta al archivo JSON que contiene la definición del mapa nodal",
        default="",
        subtype='FILE_PATH'
    )

# Clases para registrar
classes = (
    SciBlendGeometryNodesProperties,
)

def register():
    # Registrar clases
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Registrar propiedades
    bpy.types.Scene.sciblend_geonodes = PointerProperty(type=SciBlendGeometryNodesProperties)
    
    # Registrar módulos
    operators.register()
    ui.register()

def unregister():
    # Desregistrar módulos
    ui.unregister()
    operators.unregister()
    
    # Desregistrar propiedades
    del bpy.types.Scene.sciblend_geonodes
    
    # Desregistrar clases
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register() 