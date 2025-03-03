import bpy
from bpy.types import Panel

class SCIBLEND_PT_geometry_nodes_panel(Panel):
    bl_label = "SciBlend Geometry Nodes"
    bl_idname = "SCIBLEND_PT_geometry_nodes_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SciBlend'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Sección para importar JSON
        box = layout.box()
        box.label(text="Importar JSON")
        
        row = box.row()
        row.operator("sciblend.import_geometry_nodes_json", icon='FILEBROWSER')
        
        # Sección para tipos de transformaciones
        box = layout.box()
        box.label(text="Transformaciones")
        
        # Lista de transformaciones disponibles
        transformations = [
            ("translate", "Traslación", "TRANSFORM_ORIGINS"),
            ("rotate", "Rotación", "DRIVER_ROTATIONAL_DIFFERENCE"),
            ("scale", "Escala", "FULLSCREEN_ENTER"),
            ("mirror", "Espejo", "MOD_MIRROR"),
            ("array", "Array", "MOD_ARRAY"),
        ]
        
        for transform_id, transform_name, icon in transformations:
            row = box.row()
            op = row.operator("sciblend.apply_transformation", text=transform_name, icon=icon)
            op.transform_type = transform_id
        
        # Verificar si hay un archivo JSON cargado
        if hasattr(scene, "sciblend_geonodes") and scene.sciblend_geonodes.json_filepath:
            box = layout.box()
            box.label(text=f"JSON cargado: {bpy.path.basename(scene.sciblend_geonodes.json_filepath)}")

classes = (
    SCIBLEND_PT_geometry_nodes_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 