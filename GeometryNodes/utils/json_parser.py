def validate_json(data):
    """
    Valida que el JSON tenga la estructura correcta para definir un mapa nodal de Geometry Nodes.
    
    Args:
        data (dict): Datos JSON cargados
        
    Returns:
        bool: True si el JSON es válido, False en caso contrario
    """
    # Verificar que el JSON tenga las claves necesarias
    if not isinstance(data, dict):
        return False
    
    # Verificar que exista la clave 'nodes'
    if 'nodes' not in data:
        return False
    
    # Verificar que 'nodes' sea una lista
    if not isinstance(data['nodes'], list):
        return False
    
    # Verificar que exista la clave 'links'
    if 'links' not in data:
        return False
    
    # Verificar que 'links' sea una lista
    if not isinstance(data['links'], list):
        return False
    
    # Verificar cada nodo
    for node in data['nodes']:
        if not isinstance(node, dict):
            return False
        
        # Verificar que cada nodo tenga un tipo y un nombre
        if 'type' not in node or 'name' not in node:
            return False
    
    # Verificar cada enlace
    for link in data['links']:
        if not isinstance(link, dict):
            return False
        
        # Verificar que cada enlace tenga nodos y sockets de origen y destino
        required_keys = ['from_node', 'from_socket', 'to_node', 'to_socket']
        if not all(key in link for key in required_keys):
            return False
    
    return True 