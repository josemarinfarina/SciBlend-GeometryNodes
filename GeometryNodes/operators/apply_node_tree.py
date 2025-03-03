import bpy
import os
import json
import logging
from bpy.types import Operator
from bpy.props import StringProperty

from ..utils import json_parser, node_builder

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("GeometryNodes")

# Función de utilidad para inspeccionar objetos
def inspect_object(obj, name="objeto"):
    """Inspecciona un objeto y registra sus atributos y métodos"""
    logger.debug(f"Inspeccionando {name}: {obj}")
    logger.debug(f"Tipo: {type(obj)}")
    logger.debug(f"Dir: {dir(obj)}")
    if hasattr(obj, "__dict__"):
        logger.debug(f"Dict: {obj.__dict__}")

# Función para configurar un árbol de nodos de geometría
def setup_geometry_node_tree(node_tree):
    """
    Configura un árbol de nodos de geometría para asegurar que tenga nodos de entrada y salida
    correctamente conectados.
    
    Args:
        node_tree: El árbol de nodos a configurar
        
    Returns:
        tuple: (input_node, output_node) - Los nodos de entrada y salida
    """
    logger.info(f"Configurando árbol de nodos: {node_tree.name}")
    
    # Buscar nodos de entrada y salida existentes
    input_node = None
    output_node = None
    
    for node in node_tree.nodes:
        if node.type == 'GROUP_INPUT':
            input_node = node
            logger.debug(f"Nodo de entrada encontrado: {node.name}")
        elif node.type == 'GROUP_OUTPUT':
            output_node = node
            logger.debug(f"Nodo de salida encontrado: {node.name}")
    
    # Crear nodos si no existen
    if not input_node:
        logger.info("Creando nodo de entrada")
        input_node = node_tree.nodes.new('NodeGroupInput')
        input_node.location = (-200, 0)
    
    if not output_node:
        logger.info("Creando nodo de salida")
        output_node = node_tree.nodes.new('NodeGroupOutput')
        output_node.location = (200, 0)
        output_node.is_active_output = True
    else:
        output_node.is_active_output = True
    
    # Asegurar que el nodo de salida esté marcado como activo
    output_node.select = True
    node_tree.nodes.active = output_node
    
    # En Blender 4.2, debemos usar la API correcta para crear sockets
    # Verificar si hay interfaces de entrada/salida usando interface en lugar de inputs/outputs
    try:
        # Verificar si hay interfaces existentes
        has_input_interface = False
        has_output_interface = False
        
        # Verificar las interfaces existentes
        if hasattr(node_tree, 'interface') and hasattr(node_tree.interface, 'items_tree'):
            for item in node_tree.interface.items_tree:
                if hasattr(item, 'in_out'):
                    if item.in_out == 'INPUT':
                        has_input_interface = True
                        logger.debug(f"Interfaz de entrada encontrada: {item.name}")
                    elif item.in_out == 'OUTPUT':
                        has_output_interface = True
                        logger.debug(f"Interfaz de salida encontrada: {item.name}")
        
        # Si no hay interfaces, crearlas
        if not has_input_interface or not has_output_interface:
            # Limpiar interfaces existentes si es necesario
            if hasattr(node_tree, 'interface') and hasattr(node_tree.interface, 'items_tree'):
                while node_tree.interface.items_tree:
                    node_tree.interface.remove(node_tree.interface.items_tree[0])
            
            # Crear interfaces de entrada y salida
            if hasattr(node_tree, 'interface') and hasattr(node_tree.interface, 'new_socket'):
                logger.info("Creando sockets de geometría")
                
                # Crear socket de entrada
                geometry_in = node_tree.interface.new_socket(
                    name="Geometry",
                    in_out='INPUT', 
                    socket_type='NodeSocketGeometry'
                )
                logger.debug(f"Socket de entrada creado: {geometry_in}")
                
                # Crear socket de salida
                geometry_out = node_tree.interface.new_socket(
                    name="Geometry", 
                    in_out='OUTPUT',
                    socket_type='NodeSocketGeometry'
                )
                logger.debug(f"Socket de salida creado: {geometry_out}")
    except Exception as e:
        logger.error(f"Error al configurar interfaces: {str(e)}")
        # No interrumpir la ejecución, continuar con los nodos existentes
    
    return input_node, output_node

class SCIBLEND_OT_apply_geometry_nodes(Operator):
    bl_idname = "sciblend.apply_geometry_nodes"
    bl_label = "Aplicar Geometry Nodes"
    bl_description = "Aplica el mapa nodal de Geometry Nodes al objeto seleccionado"
    
    def execute(self, context):
        if not context.active_object:
            self.report({'ERROR'}, "No hay objeto seleccionado")
            return {'CANCELLED'}
        
        json_filepath = context.scene.sciblend_geonodes.json_filepath
        if not json_filepath:
            self.report({'ERROR'}, "No se ha seleccionado un archivo JSON")
            return {'CANCELLED'}
        
        try:
            # Leer el archivo JSON
            with open(bpy.path.abspath(json_filepath), 'r') as f:
                node_data = json.load(f)
            
            # Aplicar el mapa nodal
            success = self.apply_node_tree(context.active_object, node_data)
            
            if success:
                self.report({'INFO'}, "Geometry Nodes aplicado correctamente")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Error al aplicar Geometry Nodes")
                return {'CANCELLED'}
            
        except Exception as e:
            logger.exception("Error al aplicar Geometry Nodes")
            self.report({'ERROR'}, f"Error al aplicar Geometry Nodes: {str(e)}")
            return {'CANCELLED'}
    
    def apply_node_tree(self, obj, node_data):
        """
        Aplica un árbol de nodos de Geometry Nodes a un objeto.
        
        Args:
            obj: El objeto al que aplicar el árbol de nodos
            node_data: Datos del árbol de nodos en formato JSON
            
        Returns:
            bool: True si se aplicó correctamente
        """
        try:
            logger.info(f"Aplicando árbol de nodos a {obj.name}")
            
            # Añadir modificador de Geometry Nodes si no existe
            gn_mod = None
            for mod in obj.modifiers:
                if mod.type == 'NODES':
                    gn_mod = mod
                    break
            
            if not gn_mod:
                logger.info("Creando nuevo modificador GeometryNodes")
                gn_mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
            else:
                logger.info(f"Usando modificador existente: {gn_mod.name}")
            
            # Eliminar cualquier árbol de nodos existente
            if gn_mod.node_group:
                logger.info(f"Eliminando árbol de nodos existente: {gn_mod.node_group.name}")
                old_node_group = gn_mod.node_group
                gn_mod.node_group = None
                try:
                    bpy.data.node_groups.remove(old_node_group)
                    logger.info("Árbol de nodos anterior eliminado correctamente")
                except:
                    logger.warning(f"No se pudo eliminar el árbol de nodos anterior: {old_node_group.name}")
            
            # Crear un nuevo árbol de nodos desde cero
            node_tree_name = node_data.get("name", "GeometryNodes")
            logger.info(f"Creando nuevo árbol de nodos: {node_tree_name}")
            node_tree = bpy.data.node_groups.new(name=node_tree_name, type='GeometryNodeTree')
            
            # Asignar el árbol de nodos al modificador
            # Esto es crucial para que Blender configure correctamente los sockets
            logger.info("Asignando árbol de nodos al modificador")
            gn_mod.node_group = node_tree
            
            # Configurar el árbol de nodos
            input_node, output_node = setup_geometry_node_tree(node_tree)
            
            # Crear nodos según el JSON
            nodes = {}
            nodes['input'] = input_node
            nodes['output'] = output_node
            
            # Crear nodos
            logger.info("Creando nodos desde JSON")
            for node_data_item in node_data.get("nodes", []):
                try:
                    node_id = node_data_item["id"]
                    node_type = node_data_item["type"]
                    
                    # Saltar nodos de entrada y salida, ya los hemos creado
                    if node_type in ['NodeGroupInput', 'NodeGroupOutput']:
                        logger.debug(f"Saltando nodo {node_type} con ID {node_id}, ya existe")
                        continue
                    
                    node_location = node_data_item.get("location", (0, 0))
                    
                    # Crear nodo
                    logger.debug(f"Creando nodo {node_type} con ID {node_id}")
                    node = node_tree.nodes.new(node_type)
                    node.location = node_location
                    nodes[node_id] = node
                    
                    # Configurar inputs si existen
                    if "inputs" in node_data_item:
                        for input_name, input_value in node_data_item["inputs"].items():
                            try:
                                # Verificar que el input existe
                                if input_name in node.inputs:
                                    logger.debug(f"Configurando input {input_name} para nodo {node_id}")
                                    # Asignar valor según el tipo
                                    if isinstance(input_value, (list, tuple)) and len(input_value) > 0:
                                        # Para vectores y colores
                                        if hasattr(node.inputs[input_name], "default_value") and hasattr(node.inputs[input_name].default_value, "__len__"):
                                            if len(input_value) <= len(node.inputs[input_name].default_value):
                                                for i, val in enumerate(input_value):
                                                    node.inputs[input_name].default_value[i] = val
                                    else:
                                        # Para valores escalares
                                        if hasattr(node.inputs[input_name], "default_value"):
                                            node.inputs[input_name].default_value = input_value
                            except Exception as e:
                                logger.error(f"Error al configurar input {input_name}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error al crear nodo: {str(e)}")
            
            # Crear links
            logger.info("Creando links entre nodos")
            links_created = 0
            
            for link_data in node_data.get("links", []):
                try:
                    from_node_id = link_data["from_node"]
                    from_socket_name = link_data["from_socket"]
                    to_node_id = link_data["to_node"]
                    to_socket_name = link_data["to_socket"]
                    
                    logger.debug(f"Procesando link: {from_node_id}.{from_socket_name} -> {to_node_id}.{to_socket_name}")
                    
                    # Ajustar IDs para nodos de entrada y salida
                    if from_node_id == "input" or (from_node_id not in nodes and from_socket_name == "Geometry"):
                        from_node_id = "input"
                        from_socket_name = "Geometry"
                        logger.debug(f"Ajustado origen a: {from_node_id}.{from_socket_name}")
                    
                    if to_node_id == "output" or (to_node_id not in nodes and to_socket_name == "Geometry"):
                        to_node_id = "output"
                        to_socket_name = "Geometry"
                        logger.debug(f"Ajustado destino a: {to_node_id}.{to_socket_name}")
                    
                    if from_node_id in nodes and to_node_id in nodes:
                        from_node = nodes[from_node_id]
                        to_node = nodes[to_node_id]
                        
                        # Buscar sockets por nombre
                        from_socket = None
                        to_socket = None
                        
                        logger.debug(f"Buscando socket de salida '{from_socket_name}' en nodo {from_node_id}")
                        for output in from_node.outputs:
                            logger.debug(f"  - Socket de salida disponible: {output.name}")
                            if output.name == from_socket_name:
                                from_socket = output
                                logger.debug(f"  - Socket encontrado: {output.name}")
                                break
                        
                        logger.debug(f"Buscando socket de entrada '{to_socket_name}' en nodo {to_node_id}")
                        for input in to_node.inputs:
                            logger.debug(f"  - Socket de entrada disponible: {input.name}")
                            if input.name == to_socket_name:
                                to_socket = input
                                logger.debug(f"  - Socket encontrado: {input.name}")
                                break
                        
                        # Si no se encontraron por nombre, intentar por índice
                        if from_socket is None and from_socket_name.isdigit():
                            idx = int(from_socket_name)
                            if idx < len(from_node.outputs):
                                from_socket = from_node.outputs[idx]
                                logger.debug(f"Socket de salida encontrado por índice: {idx}")
                        
                        if to_socket is None and to_socket_name.isdigit():
                            idx = int(to_socket_name)
                            if idx < len(to_node.inputs):
                                to_socket = to_node.inputs[idx]
                                logger.debug(f"Socket de entrada encontrado por índice: {idx}")
                        
                        # Crear link si se encontraron los sockets
                        if from_socket and to_socket:
                            logger.debug(f"Creando link: {from_node_id}.{from_socket.name} -> {to_node_id}.{to_socket.name}")
                            node_tree.links.new(from_socket, to_socket)
                            links_created += 1
                        else:
                            logger.warning(f"No se pudieron encontrar los sockets para el link: {from_node_id}.{from_socket_name} -> {to_node_id}.{to_socket_name}")
                except Exception as e:
                    logger.error(f"Error al crear link: {str(e)}")
            
            # Si no hay links, conectar directamente entrada y salida
            if links_created == 0:
                logger.info("No hay links, conectando directamente entrada y salida")
                try:
                    if len(input_node.outputs) > 0 and len(output_node.inputs) > 0:
                        logger.debug(f"Conectando {input_node.outputs[0].name} -> {output_node.inputs[0].name}")
                        node_tree.links.new(input_node.outputs[0], output_node.inputs[0])
                        links_created += 1
                    else:
                        logger.warning("No se pueden conectar entrada y salida: no hay sockets disponibles")
                        if len(input_node.outputs) == 0:
                            logger.warning("El nodo de entrada no tiene sockets de salida")
                        if len(output_node.inputs) == 0:
                            logger.warning("El nodo de salida no tiene sockets de entrada")
                except Exception as e:
                    logger.error(f"Error al conectar entrada y salida: {str(e)}")
            
            # Verificar los links creados
            logger.info(f"Links creados: {links_created}")
            for i, link in enumerate(node_tree.links):
                logger.debug(f"Link {i}: {link.from_node.name}.{link.from_socket.name} -> {link.to_node.name}.{link.to_socket.name}")
            
            # Forzar actualización
            try:
                logger.info("Forzando actualización del modificador")
                # Forzar actualización del modificador
                gn_mod.show_viewport = False
                gn_mod.show_viewport = True
            except Exception as e:
                logger.error(f"Error al actualizar: {str(e)}")
            
            logger.info("Árbol de nodos aplicado correctamente")
            return True
        
        except Exception as e:
            logger.exception(f"Error al aplicar Geometry Nodes: {str(e)}")
            return False

class SCIBLEND_OT_apply_transformation(Operator):
    bl_idname = "sciblend.apply_transformation"
    bl_label = "Aplicar Transformación"
    bl_description = "Aplica una transformación específica usando Geometry Nodes"
    
    transform_type: StringProperty(
        name="Tipo de Transformación",
        description="Tipo de transformación a aplicar",
        default="translate"
    )
    
    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No hay un objeto activo seleccionado")
            return {'CANCELLED'}
        
        # Obtener el tipo de transformación y atributo del panel
        props = context.scene.sciblend_geonodes
        self.transform_type = props.transform_type
        attribute_target = props.attribute_target
        
        # Crear datos de nodo según el tipo de transformación
        node_data = self.create_transform_node_data(attribute_target)
        
        # Aplicar el árbol de nodos
        success = self.apply_node_tree(obj, node_data)
        
        if success:
            self.report({'INFO'}, f"Transformación {self.transform_type} aplicada correctamente")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Error al aplicar transformación {self.transform_type}")
            return {'CANCELLED'}
    
    def create_transform_node_data(self, attribute_target):
        """
        Crea los datos de nodo para la transformación especificada.
        
        Args:
            attribute_target: El atributo al que se aplicará la transformación
            
        Returns:
            dict: Los datos del nodo en formato JSON
        """
        # Obtener el nombre del atributo personalizado si es necesario
        props = bpy.context.scene.sciblend_geonodes
        custom_attribute_name = ""
        
        if attribute_target == 'CUSTOM':
            custom_attribute_name = props.custom_attribute_name
            if not custom_attribute_name:
                logger.warning("Se seleccionó atributo personalizado pero no se especificó un nombre")
        
        # Nodos básicos para todas las transformaciones
        node_data = {
            "name": f"GN_{self.transform_type}",
            "nodes": [],
            "links": []
        }
        
        # Configuración específica según el tipo de transformación
        if self.transform_type in ['translate', 'rotate', 'scale']:
            # Para transformaciones básicas, usamos GeometryNodeTransform
            transform_node = {
                "type": "GeometryNodeTransform",
                "name": f"Transform_{self.transform_type}",
                "location": (0, 0),
                "properties": {}
            }
            node_data["nodes"].append(transform_node)
            
            # Enlaces básicos para geometría completa
            if attribute_target == 'GEOMETRY':
                node_data["links"] = [
                    {
                        "from_node": "GROUP_INPUT",
                        "from_socket": "Geometry",
                        "to_node": f"Transform_{self.transform_type}",
                        "to_socket": "Geometry"
                    },
                    {
                        "from_node": f"Transform_{self.transform_type}",
                        "from_socket": "Geometry",
                        "to_node": "GROUP_OUTPUT",
                        "to_socket": "Geometry"
                    }
                ]
            else:
                # Para atributos específicos, necesitamos nodos adicionales
                # Nodo para capturar el atributo
                capture_node = {
                    "type": "GeometryNodeCaptureAttribute",
                    "name": "CaptureAttribute",
                    "location": (-200, 0),
                    "properties": {
                        "data_type": 'FLOAT_VECTOR'  # Tipo por defecto para posiciones, normales, etc.
                    }
                }
                
                # Nodo para transferir el atributo transformado
                transfer_node = {
                    "type": "GeometryNodeStoreNamedAttribute",
                    "name": "StoreAttribute",
                    "location": (200, 0),
                    "properties": {}
                }
                
                # Añadir nodos al árbol
                node_data["nodes"].extend([capture_node, transfer_node])
                
                # Configurar el nombre del atributo según el tipo seleccionado
                attribute_name = ""
                if attribute_target == 'POSITION':
                    attribute_name = "position"
                elif attribute_target == 'NORMAL':
                    attribute_name = "normal"
                elif attribute_target == 'UV':
                    attribute_name = "UVMap"
                elif attribute_target == 'COLOR':
                    attribute_name = "Color"
                elif attribute_target == 'CUSTOM' and custom_attribute_name:
                    attribute_name = custom_attribute_name
                
                # Configurar propiedades de los nodos según el atributo
                capture_node["properties"]["attribute_name"] = attribute_name
                transfer_node["properties"]["name"] = attribute_name
                
                # Enlaces para el flujo de atributos
                node_data["links"] = [
                    # Conectar la geometría de entrada al nodo de captura
                    {
                        "from_node": "GROUP_INPUT",
                        "from_socket": "Geometry",
                        "to_node": "CaptureAttribute",
                        "to_socket": "Geometry"
                    },
                    # Conectar el atributo capturado al nodo de transformación
                    {
                        "from_node": "CaptureAttribute",
                        "from_socket": "Attribute",
                        "to_node": f"Transform_{self.transform_type}",
                        "to_socket": "Geometry"
                    },
                    # Conectar la geometría transformada al nodo de transferencia
                    {
                        "from_node": f"Transform_{self.transform_type}",
                        "from_socket": "Geometry",
                        "to_node": "StoreAttribute",
                        "to_socket": "Value"
                    },
                    # Conectar la geometría del nodo de captura al nodo de transferencia
                    {
                        "from_node": "CaptureAttribute",
                        "from_socket": "Geometry",
                        "to_node": "StoreAttribute",
                        "to_socket": "Geometry"
                    },
                    # Conectar la geometría final a la salida
                    {
                        "from_node": "StoreAttribute",
                        "from_socket": "Geometry",
                        "to_node": "GROUP_OUTPUT",
                        "to_socket": "Geometry"
                    }
                ]
        elif self.transform_type == 'mirror':
            # Para espejo, usamos un nodo específico si está disponible
            try:
                # Intentar crear un nodo de espejo
                mirror_node = {
                    "type": "GeometryNodeMirror",  # Este nodo puede no existir en todas las versiones
                    "name": "Mirror",
                    "location": (0, 0),
                    "properties": {}
                }
                node_data["nodes"].append(mirror_node)
                
                # Enlaces para el nodo de espejo
                node_data["links"] = [
                    {
                        "from_node": "GROUP_INPUT",
                        "from_socket": "Geometry",
                        "to_node": "Mirror",
                        "to_socket": "Geometry"
                    },
                    {
                        "from_node": "Mirror",
                        "from_socket": "Geometry",
                        "to_node": "GROUP_OUTPUT",
                        "to_socket": "Geometry"
                    }
                ]
            except Exception as e:
                logger.error(f"Error al crear nodo de espejo: {str(e)}")
                # Si falla, conectar directamente entrada y salida
                node_data["links"] = [
                    {
                        "from_node": "GROUP_INPUT",
                        "from_socket": "Geometry",
                        "to_node": "GROUP_OUTPUT",
                        "to_socket": "Geometry"
                    }
                ]
        elif self.transform_type == 'array':
            # Para array, usamos un nodo de instancias
            array_node = {
                "type": "GeometryNodeInstanceOnPoints",
                "name": "Array",
                "location": (0, 0),
                "properties": {}
            }
            
            # Nodo para crear puntos en una línea
            points_node = {
                "type": "GeometryNodeMeshLine",
                "name": "Points",
                "location": (-200, -100),
                "properties": {
                    "count_mode": 'TOTAL',
                    "count": 5
                }
            }
            
            node_data["nodes"].extend([array_node, points_node])
            
            # Enlaces para el nodo de array
            node_data["links"] = [
                {
                    "from_node": "GROUP_INPUT",
                    "from_socket": "Geometry",
                    "to_node": "Array",
                    "to_socket": "Instance"
                },
                {
                    "from_node": "Points",
                    "from_socket": "Mesh",
                    "to_node": "Array",
                    "to_socket": "Points"
                },
                {
                    "from_node": "Array",
                    "from_socket": "Instances",
                    "to_node": "GROUP_OUTPUT",
                    "to_socket": "Geometry"
                }
            ]
        
        return node_data
    
    def apply_node_tree(self, obj, node_data):
        """
        Aplica un árbol de nodos de Geometry Nodes a un objeto.
        
        Args:
            obj: El objeto al que aplicar el árbol de nodos
            node_data: Datos del árbol de nodos (no se usa, se crea según self.transform_type)
            
        Returns:
            bool: True si se aplicó correctamente
        """
        try:
            logger.info(f"Aplicando transformación {self.transform_type} a {obj.name}")
            
            # Añadir modificador de Geometry Nodes si no existe
            gn_mod = None
            for mod in obj.modifiers:
                if mod.type == 'NODES':
                    gn_mod = mod
                    break
            
            if not gn_mod:
                logger.info("Creando nuevo modificador GeometryNodes")
                gn_mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
            else:
                logger.info(f"Usando modificador existente: {gn_mod.name}")
            
            # Eliminar cualquier árbol de nodos existente
            if gn_mod.node_group:
                logger.info(f"Eliminando árbol de nodos existente: {gn_mod.node_group.name}")
                old_node_group = gn_mod.node_group
                gn_mod.node_group = None
                try:
                    bpy.data.node_groups.remove(old_node_group)
                    logger.info("Árbol de nodos anterior eliminado correctamente")
                except:
                    logger.warning(f"No se pudo eliminar el árbol de nodos anterior: {old_node_group.name}")
            
            # Crear un nuevo árbol de nodos
            node_tree_name = f"GN_{self.transform_type}"
            logger.info(f"Creando nuevo árbol de nodos: {node_tree_name}")
            node_tree = bpy.data.node_groups.new(name=node_tree_name, type='GeometryNodeTree')
            
            # Asignar el árbol de nodos al modificador
            # Esto es crucial para que Blender configure correctamente los sockets
            logger.info("Asignando árbol de nodos al modificador")
            gn_mod.node_group = node_tree
            
            # Configurar el árbol de nodos
            input_node, output_node = setup_geometry_node_tree(node_tree)
            
            # Variable para el nodo de transformación
            transform_node = None
            
            # Crear nodo de transformación según el tipo
            try:
                logger.info(f"Creando nodo de transformación para tipo: {self.transform_type}")
                
                if self.transform_type == "translate":
                    # Crear nodo de transformación
                    logger.debug("Creando nodo GeometryNodeTransform para traslación")
                    transform_node = node_tree.nodes.new('GeometryNodeTransform')
                    transform_node.location = (100, 0)
                    
                    # Intentar configurar valores
                    try:
                        if len(transform_node.inputs) > 1:
                            logger.debug("Configurando traslación en X")
                            transform_node.inputs[1].default_value = (1, 0, 0)  # Traslación en X
                    except Exception as e:
                        logger.error(f"Error al configurar traslación: {str(e)}")
                    
                elif self.transform_type == "rotate":
                    # Crear nodo de transformación
                    logger.debug("Creando nodo GeometryNodeTransform para rotación")
                    transform_node = node_tree.nodes.new('GeometryNodeTransform')
                    transform_node.location = (100, 0)
                    
                    # Intentar configurar valores
                    try:
                        if len(transform_node.inputs) > 2:
                            logger.debug("Configurando rotación en Z")
                            transform_node.inputs[2].default_value = (0, 0, 0.785398)  # Rotación 45 grados en Z
                    except Exception as e:
                        logger.error(f"Error al configurar rotación: {str(e)}")
                    
                elif self.transform_type == "scale":
                    # Crear nodo de transformación
                    logger.debug("Creando nodo GeometryNodeTransform para escala")
                    transform_node = node_tree.nodes.new('GeometryNodeTransform')
                    transform_node.location = (100, 0)
                    
                    # Intentar configurar valores
                    try:
                        if len(transform_node.inputs) > 3:
                            logger.debug("Configurando escala x2")
                            transform_node.inputs[3].default_value = (2, 2, 2)  # Escala x2
                    except Exception as e:
                        logger.error(f"Error al configurar escala: {str(e)}")
                    
                elif self.transform_type == "mirror":
                    # Crear nodo de espejo
                    logger.debug("Creando nodo GeometryNodeMirror")
                    transform_node = node_tree.nodes.new('GeometryNodeMirror')
                    transform_node.location = (100, 0)
                    
                    # Intentar configurar valores
                    try:
                        if len(transform_node.inputs) > 1:
                            logger.debug("Configurando espejo en X")
                            transform_node.inputs[1].default_value = True  # Espejo en X
                    except Exception as e:
                        logger.error(f"Error al configurar espejo: {str(e)}")
                    
                elif self.transform_type == "array":
                    # Para array, necesitamos un enfoque diferente
                    logger.debug("Creando nodos para array")
                    
                    # Primero creamos una línea de puntos
                    logger.debug("Creando nodo GeometryNodeMeshLine")
                    line_node = node_tree.nodes.new('GeometryNodeMeshLine')
                    line_node.location = (-50, -100)
                    
                    # Intentar configurar valores
                    try:
                        if len(line_node.inputs) > 0:
                            logger.debug("Configurando número de puntos: 5")
                            line_node.inputs[0].default_value = 5  # 5 puntos
                        if len(line_node.inputs) > 1:
                            logger.debug("Configurando longitud: 2.0")
                            line_node.inputs[1].default_value = 2.0  # Longitud 2
                    except Exception as e:
                        logger.error(f"Error al configurar línea: {str(e)}")
                    
                    # Luego creamos un nodo para instanciar en esos puntos
                    logger.debug("Creando nodo GeometryNodeInstanceOnPoints")
                    transform_node = node_tree.nodes.new('GeometryNodeInstanceOnPoints')
                    transform_node.location = (100, 0)
                    
                    # Conectar nodos específicos de array
                    try:
                        logger.debug("Conectando nodos de array")
                        if len(line_node.outputs) > 0 and len(transform_node.inputs) > 0:
                            logger.debug(f"Conectando {line_node.outputs[0].name} -> {transform_node.inputs[0].name}")
                            node_tree.links.new(line_node.outputs[0], transform_node.inputs[0])  # Puntos
                        
                        if len(input_node.outputs) > 0 and len(transform_node.inputs) > 2:
                            logger.debug(f"Conectando {input_node.outputs[0].name} -> {transform_node.inputs[2].name}")
                            node_tree.links.new(input_node.outputs[0], transform_node.inputs[2])  # Instancia
                    except Exception as e:
                        logger.error(f"Error al conectar nodos de array: {str(e)}")
                
                # Inspeccionar el nodo de transformación
                if transform_node:
                    inspect_object(transform_node, "transform_node")
                
            except Exception as e:
                logger.error(f"Error al crear nodo de transformación: {str(e)}")
            
            # Conectar nodos si se creó un nodo de transformación
            links_created = 0
            try:
                logger.info("Conectando nodos")
                if transform_node:
                    # Para todos excepto array que ya tiene sus conexiones específicas
                    if self.transform_type != "array":
                        if len(input_node.outputs) > 0 and len(transform_node.inputs) > 0:
                            logger.debug(f"Conectando {input_node.outputs[0].name} -> {transform_node.inputs[0].name}")
                            node_tree.links.new(input_node.outputs[0], transform_node.inputs[0])
                            links_created += 1
                    
                    # Conectar la salida del nodo de transformación al nodo de salida
                    if len(transform_node.outputs) > 0 and len(output_node.inputs) > 0:
                        logger.debug(f"Conectando {transform_node.outputs[0].name} -> {output_node.inputs[0].name}")
                        node_tree.links.new(transform_node.outputs[0], output_node.inputs[0])
                        links_created += 1
                else:
                    # Si no se creó ningún nodo de transformación, conectar directamente entrada y salida
                    logger.warning("No se creó nodo de transformación, conectando directamente entrada y salida")
                    if len(input_node.outputs) > 0 and len(output_node.inputs) > 0:
                        logger.debug(f"Conectando {input_node.outputs[0].name} -> {output_node.inputs[0].name}")
                        node_tree.links.new(input_node.outputs[0], output_node.inputs[0])
                        links_created += 1
            except Exception as e:
                logger.error(f"Error al conectar nodos: {str(e)}")
                # Intentar conectar directamente entrada y salida como fallback
                try:
                    logger.warning("Intentando conectar directamente entrada y salida como fallback")
                    if len(input_node.outputs) > 0 and len(output_node.inputs) > 0:
                        logger.debug(f"Conectando {input_node.outputs[0].name} -> {output_node.inputs[0].name}")
                        node_tree.links.new(input_node.outputs[0], output_node.inputs[0])
                        links_created += 1
                except Exception as e2:
                    logger.error(f"Error al conectar entrada y salida: {str(e2)}")
            
            # Verificar los links creados
            logger.info(f"Links creados: {links_created}")
            for i, link in enumerate(node_tree.links):
                logger.debug(f"Link {i}: {link.from_node.name}.{link.from_socket.name} -> {link.to_node.name}.{link.to_socket.name}")
            
            # Forzar actualización
            try:
                logger.info("Forzando actualización del modificador")
                # Forzar actualización del modificador
                gn_mod.show_viewport = False
                gn_mod.show_viewport = True
            except Exception as e:
                logger.error(f"Error al actualizar: {str(e)}")
            
            logger.info(f"Transformación {self.transform_type} aplicada correctamente")
            return True
            
        except Exception as e:
            logger.exception(f"Error al aplicar transformación: {str(e)}")
            return False

classes = (
    SCIBLEND_OT_apply_geometry_nodes,
    SCIBLEND_OT_apply_transformation,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 