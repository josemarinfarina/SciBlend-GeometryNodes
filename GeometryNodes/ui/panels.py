import bpy
from bpy.types import Panel

class SCIBLEND_PT_geometry_nodes(Panel):
    bl_label = "SciBlend Geometry Nodes"
    bl_idname = "SCIBLEND_PT_geometry_nodes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SciBlend'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sciblend_geonodes
        
        # Sección para aplicar transformaciones predefinidas
        box = layout.box()
        box.label(text="Transformaciones Predefinidas")
        
        # Selector de transformación
        row = box.row()
        row.prop(props, "transform_type", text="Tipo")
        
        # Selector de atributo
        row = box.row()
        row.prop(props, "attribute_target", text="Aplicar a")
        
        # Si se selecciona "Atributo personalizado", mostrar campo para el nombre
        if props.attribute_target == 'CUSTOM':
            row = box.row()
            row.prop(props, "custom_attribute_name", text="Nombre")
        
        # Botón para aplicar la transformación
        row = box.row()
        row.operator("sciblend.apply_transformation", text="Aplicar Transformación")
        
        # Sección para cargar JSON personalizado
        box = layout.box()
        box.label(text="Cargar JSON Personalizado")
        
        # Campo para seleccionar archivo JSON
        box.prop(props, "json_filepath", text="")
        
        # Botón para aplicar el JSON
        row = box.row()
        row.operator("sciblend.apply_geometry_nodes", text="Aplicar Geometry Nodes")

def register():
    bpy.utils.register_class(SCIBLEND_PT_geometry_nodes)

def unregister():
    bpy.utils.unregister_class(SCIBLEND_PT_geometry_nodes) 