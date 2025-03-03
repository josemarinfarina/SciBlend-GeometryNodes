import bpy
import os
import sys
import importlib
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import PropertyGroup
from . import operators
from . import ui
from . import utils

bl_info = {
    "name": "SciBlend - Geometry Nodes",
    "author": "SciBlend Team",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > SciBlend",
    "description": "Herramientas para aplicar Geometry Nodes a objetos",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

def unregister_old_addon():
    """
    Desregistra cualquier versión anterior del addon que pueda estar registrada.
    Esto permite actualizar el addon sin necesidad de reiniciar Blender.
    """
    # Configurar logging
    import logging
    logger = logging.getLogger("GeometryNodes")
    
    # Lista de clases a desregistrar
    classes_to_unregister = [
        # Operadores
        "SCIBLEND_OT_apply_geometry_nodes",
        "SCIBLEND_OT_apply_transformation",
        # UI
        "SCIBLEND_PT_geometry_nodes",
        # Propiedades
        "SciblendGeonodesProperties"
    ]
    
    # Desregistrar clases
    for class_name in classes_to_unregister:
        try:
            # Intentar obtener la clase por su nombre
            cls = getattr(bpy.types, class_name, None)
            if cls is not None:
                logger.info(f"Desregistrando clase: {class_name}")
                bpy.utils.unregister_class(cls)
        except Exception as e:
            # Ignorar errores, ya que la clase puede no estar registrada
            logger.debug(f"Error al desregistrar {class_name}: {str(e)}")
    
    # Desregistrar propiedades
    try:
        if hasattr(bpy.types.Scene, "sciblend_geonodes"):
            logger.info("Desregistrando propiedad: sciblend_geonodes")
            del bpy.types.Scene.sciblend_geonodes
    except Exception as e:
        logger.debug(f"Error al desregistrar propiedad sciblend_geonodes: {str(e)}")
    
    # Recargar módulos
    try:
        # Recargar módulos para asegurar que se usen las versiones más recientes
        for module in [operators, ui, utils]:
            logger.info(f"Recargando módulo: {module.__name__}")
            importlib.reload(module)
    except Exception as e:
        logger.debug(f"Error al recargar módulos: {str(e)}")
    
    logger.info("Desregistro de versiones anteriores completado")

class SciblendGeonodesProperties(PropertyGroup):
    json_filepath: StringProperty(
        name="Archivo JSON",
        description="Ruta al archivo JSON con la definición del árbol de nodos",
        default="",
        subtype='FILE_PATH'
    )
    
    transform_type: EnumProperty(
        name="Tipo de Transformación",
        description="Tipo de transformación a aplicar",
        items=[
            ('translate', "Trasladar", "Aplicar traslación"),
            ('rotate', "Rotar", "Aplicar rotación"),
            ('scale', "Escalar", "Aplicar escalado")
        ],
        default='translate'
    )

def register():
    # Desregistrar cualquier versión anterior del addon
    unregister_old_addon()
    
    # Registrar clases
    bpy.utils.register_class(SciblendGeonodesProperties)
    
    # Registrar operadores y UI
    operators.register()
    ui.register()
    
    # Registrar propiedades
    bpy.types.Scene.sciblend_geonodes = bpy.props.PointerProperty(type=SciblendGeonodesProperties)
    
    print("SciBlend - Geometry Nodes registrado correctamente")

def unregister():
    # Desregistrar propiedades
    del bpy.types.Scene.sciblend_geonodes
    
    # Desregistrar operadores y UI
    ui.unregister()
    operators.unregister()
    
    # Desregistrar clases
    bpy.utils.unregister_class(SciblendGeonodesProperties)
    
    print("SciBlend - Geometry Nodes desregistrado correctamente")

if __name__ == "__main__":
    register() 