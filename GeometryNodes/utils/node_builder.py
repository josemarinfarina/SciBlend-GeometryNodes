import bpy

def build_and_apply_node_tree(obj, data):
    """
    Construye y aplica un árbol de nodos de Geometry Nodes a un objeto
    a partir de datos JSON.
    
    Args:
        obj: El objeto al que aplicar el árbol de nodos
        data: Diccionario con los datos del árbol de nodos
    
    Returns:
        bool: True si se aplicó correctamente, False en caso contrario
    """
    try:
        # Añadir modificador de Geometry Nodes si no existe
        gn_mod = None
        for mod in obj.modifiers:
            if mod.type == 'NODES':
                gn_mod = mod
                break
        
        if not gn_mod:
            gn_mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
        
        # Eliminar cualquier árbol de nodos existente
        if gn_mod.node_group:
            old_node_group = gn_mod.node_group
            gn_mod.node_group = None
            try:
                bpy.data.node_groups.remove(old_node_group)
            except:
                print(f"No se pudo eliminar el árbol de nodos anterior: {old_node_group.name}")
        
        # Crear un nuevo árbol de nodos desde cero
        node_tree = bpy.data.node_groups.new(name=data.get("name", "GeometryNodes"), type='GeometryNodeTree')
        
        # Asignar el árbol de nodos al modificador
        gn_mod.node_group = node_tree
        
        # Crear nodos de entrada y salida básicos
        input_node = node_tree.nodes.new('NodeGroupInput')
        input_node.location = (-400, 0)
        
        output_node = node_tree.nodes.new('NodeGroupOutput')
        output_node.location = (400, 0)
        output_node.is_active_output = True
        
        # Intentar crear interfaces del árbol de nodos
        try:
            # Crear las interfaces del árbol de nodos (para Blender 2.93+)
            if hasattr(node_tree, 'inputs') and hasattr(node_tree, 'outputs'):
                geometry_in = node_tree.inputs.new('NodeSocketGeometry', "Geometry")
                geometry_out = node_tree.outputs.new('NodeSocketGeometry', "Geometry")
        except Exception as e:
            print(f"No se pudieron crear interfaces: {str(e)}")
            # En versiones más recientes, las interfaces se crean automáticamente
        
        # Crear nodos según el JSON
        nodes = {}
        nodes['input'] = input_node
        nodes['output'] = output_node
        
        for node_data in data.get("nodes", []):
            node_id = node_data["id"]
            node_type = node_data["type"]
            
            # Saltar nodos de entrada y salida, ya los hemos creado
            if node_type in ['NodeGroupInput', 'NodeGroupOutput']:
                continue
                
            node_location = node_data.get("location", (0, 0))
            
            # Crear nodo
            try:
                node = node_tree.nodes.new(node_type)
                node.location = node_location
                nodes[node_id] = node
                
                # Configurar inputs si existen
                if "inputs" in node_data:
                    for input_name, input_value in node_data["inputs"].items():
                        if input_name in node.inputs:
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
                print(f"Error al crear nodo {node_type}: {str(e)}")
        
        # Crear links
        for link_data in data.get("links", []):
            try:
                from_node_id = link_data["from_node"]
                from_socket_name = link_data["from_socket"]
                to_node_id = link_data["to_node"]
                to_socket_name = link_data["to_socket"]
                
                # Ajustar IDs para nodos de entrada y salida
                if from_node_id == "input" or (from_node_id not in nodes and from_socket_name == "Geometry"):
                    from_node_id = "input"
                    from_socket_name = "Geometry"
                
                if to_node_id == "output" or (to_node_id not in nodes and to_socket_name == "Geometry"):
                    to_node_id = "output"
                    to_socket_name = "Geometry"
                
                if from_node_id in nodes and to_node_id in nodes:
                    from_node = nodes[from_node_id]
                    to_node = nodes[to_node_id]
                    
                    # Buscar sockets por nombre
                    from_socket = None
                    to_socket = None
                    
                    for output in from_node.outputs:
                        if output.name == from_socket_name:
                            from_socket = output
                            break
                    
                    for input in to_node.inputs:
                        if input.name == to_socket_name:
                            to_socket = input
                            break
                    
                    # Si no se encontraron por nombre, intentar por índice
                    if from_socket is None and from_socket_name.isdigit():
                        idx = int(from_socket_name)
                        if idx < len(from_node.outputs):
                            from_socket = from_node.outputs[idx]
                    
                    if to_socket is None and to_socket_name.isdigit():
                        idx = int(to_socket_name)
                        if idx < len(to_node.inputs):
                            to_socket = to_node.inputs[idx]
                    
                    # Crear link si se encontraron los sockets
                    if from_socket and to_socket:
                        node_tree.links.new(from_socket, to_socket)
            except Exception as e:
                print(f"Error al crear link: {str(e)}")
        
        # Si no hay links, conectar directamente entrada y salida
        if len(node_tree.links) == 0:
            try:
                # Intentar conectar el primer socket de salida del nodo de entrada
                # con el primer socket de entrada del nodo de salida
                if len(input_node.outputs) > 0 and len(output_node.inputs) > 0:
                    node_tree.links.new(input_node.outputs[0], output_node.inputs[0])
            except Exception as e:
                print(f"Error al crear link directo: {str(e)}")
        
        # Asegurarse de que el nodo de salida esté marcado como activo
        for node in node_tree.nodes:
            if node.type == 'GROUP_OUTPUT':
                node.is_active_output = True
        
        # Intentar actualizar la interfaz para reflejar los cambios
        try:
            if hasattr(bpy.context, 'view_layer'):
                bpy.context.view_layer.update()
        except Exception as e:
            print(f"Error al actualizar view_layer: {str(e)}")
        
        return True
    
    except Exception as e:
        print(f"Error al construir el árbol de nodos: {str(e)}")
        return False

def setup_node_tree_io(node_group):
    """
    Configura los nodos de entrada y salida en un árbol de nodos de Geometry Nodes.
    
    Args:
        node_group (bpy.types.NodeTree): Árbol de nodos a configurar
    """
    # Crear nodo de entrada si no existe
    input_node = None
    output_node = None
    
    for node in node_group.nodes:
        if node.type == 'GROUP_INPUT':
            input_node = node
        elif node.type == 'GROUP_OUTPUT':
            output_node = node
    
    if input_node is None:
        input_node = node_group.nodes.new(type='NodeGroupInput')
        input_node.location = (-600, 0)
    
    if output_node is None:
        output_node = node_group.nodes.new(type='NodeGroupOutput')
        output_node.location = (600, 0)
    
    # Asegurarse de que hay una entrada de geometría
    if 'Geometry' not in [input.name for input in node_group.inputs]:
        node_group.inputs.new('NodeSocketGeometry', "Geometry")
    
    # Asegurarse de que hay una salida de geometría
    if 'Geometry' not in [output.name for output in node_group.outputs]:
        node_group.outputs.new('NodeSocketGeometry', "Geometry")

def create_nodes(node_group, nodes_data):
    """
    Crea los nodos en un árbol de nodos de Geometry Nodes según los datos JSON.
    
    Args:
        node_group (bpy.types.NodeTree): Árbol de nodos donde crear los nodos
        nodes_data (list): Lista de diccionarios con datos de nodos
        
    Returns:
        dict: Mapeo de IDs de nodos en el JSON a nodos creados en Blender
    """
    node_map = {}
    
    for node_data in nodes_data:
        # Obtener el tipo de nodo
        node_type = node_data['type']
        
        # Crear el nodo
        node = node_group.nodes.new(type=node_type)
        node.name = node_data['name']
        
        # Establecer la posición del nodo
        if 'location' in node_data:
            node.location = (node_data['location'][0], node_data['location'][1])
        
        # Configurar propiedades del nodo
        if 'properties' in node_data:
            for prop_name, prop_value in node_data['properties'].items():
                if hasattr(node, prop_name):
                    setattr(node, prop_name, prop_value)
        
        # Configurar entradas del nodo
        if 'inputs' in node_data:
            for i, input_value in enumerate(node_data['inputs']):
                if i < len(node.inputs) and hasattr(node.inputs[i], 'default_value'):
                    node.inputs[i].default_value = input_value
        
        # Guardar el nodo en el mapeo
        node_map[node_data.get('id', node_data['name'])] = node
    
    return node_map

def create_links(node_group, links_data, node_map):
    """
    Crea los enlaces entre nodos en un árbol de nodos de Geometry Nodes según los datos JSON.
    
    Args:
        node_group (bpy.types.NodeTree): Árbol de nodos donde crear los enlaces
        links_data (list): Lista de diccionarios con datos de enlaces
        node_map (dict): Mapeo de IDs de nodos en el JSON a nodos creados en Blender
    """
    for link_data in links_data:
        # Obtener los nodos de origen y destino
        from_node_id = link_data['from_node']
        to_node_id = link_data['to_node']
        
        if from_node_id not in node_map or to_node_id not in node_map:
            continue
        
        from_node = node_map[from_node_id]
        to_node = node_map[to_node_id]
        
        # Obtener los sockets de origen y destino
        from_socket_name = link_data['from_socket']
        to_socket_name = link_data['to_socket']
        
        # Encontrar los sockets por nombre o índice
        from_socket = None
        to_socket = None
        
        # Intentar encontrar por nombre
        for socket in from_node.outputs:
            if socket.name == from_socket_name:
                from_socket = socket
                break
        
        for socket in to_node.inputs:
            if socket.name == to_socket_name:
                to_socket = socket
                break
        
        # Si no se encontró por nombre, intentar por índice
        if from_socket is None and from_socket_name.isdigit():
            idx = int(from_socket_name)
            if idx < len(from_node.outputs):
                from_socket = from_node.outputs[idx]
        
        if to_socket is None and to_socket_name.isdigit():
            idx = int(to_socket_name)
            if idx < len(to_node.inputs):
                to_socket = to_node.inputs[idx]
        
        # Crear el enlace si se encontraron los sockets
        if from_socket is not None and to_socket is not None:
            node_group.links.new(from_socket, to_socket) 