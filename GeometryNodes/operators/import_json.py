import bpy
import json
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty

from ..utils import json_parser

class SCIBLEND_OT_import_geometry_nodes_json(Operator, ImportHelper):
    bl_idname = "sciblend.import_geometry_nodes_json"
    bl_label = "Seleccionar JSON"
    bl_description = "Selecciona un archivo JSON con la definición del mapa nodal"
    
    filename_ext = ".json"
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    
    def execute(self, context):
        try:
            # Guardar la ruta del archivo seleccionado
            context.scene.sciblend_geonodes.json_filepath = self.filepath
            
            # Intentar leer el archivo para verificar que es válido
            with open(self.filepath, 'r') as f:
                json.load(f)
            
            self.report({'INFO'}, f"JSON cargado: {bpy.path.basename(self.filepath)}")
            return {'FINISHED'}
            
        except json.JSONDecodeError:
            self.report({'ERROR'}, "El archivo seleccionado no es un JSON válido")
            return {'CANCELLED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error al cargar el archivo: {str(e)}")
            return {'CANCELLED'}

classes = (
    SCIBLEND_OT_import_geometry_nodes_json,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 