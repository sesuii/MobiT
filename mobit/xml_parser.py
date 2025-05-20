import xml.etree.ElementTree as ET
import json

def find_content(element):
    """Extract relevant content from an XML element."""
    attributes_to_check = ['resource-id', 'text', 'content-desc', 'class']
    content = []

    for attr in attributes_to_check:
        value = element.attrib.get(attr)
        if value:
            if attr == 'class':
                value = value.replace('android.widget.', '').replace('android.view.', '')
            content.append(value)

    for child in element:
        content.append(find_content(child))

    return ' '.join(content)

def add_element(tree, array, element, index):
    """Recursively add an XML element and its attributes to the tree and array."""
    tree_item = {}
    array_item = {}
    tree.append(tree_item)
    array.append(array_item)

    # List of attributes to include
    attributes = ['bounds', 'clickable', 'text', 'resource-id', 'class', 'content-desc']

    for attr in attributes:
        value = element.attrib.get(attr)
        if value:
            if attr == 'class':
                value = value.replace('android.widget.', '').replace('android.view.', '')
            tree_item[attr] = array_item[attr] = value

    tree_item['index'] = array_item['index'] = index

    for child in element:
        if 'children' not in tree_item:
            tree_item['children'] = []
        child_index = f"{index}-{child.get('index')}"
        add_element(tree_item['children'], array, child, child_index)

def find_element(array, index):
    """Find an element by its index in the given array."""
    for element in array:
        if element.get('index') == index:
            return element
    return None

def find_node(json_filepath, index):
    """Find and return a node from the JSON file by index."""
    with open(json_filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return find_element(data.get('array', []), index)

def find_container_by_index(src_file, index):
    """Retrieve information about the container element by its index."""
    with open(src_file, 'r', encoding='utf-8') as file:
        json_elements = json.load(file)
    
    container = find_element(json_elements[0], index)
    if not container:
        return None

    bounds = container.get('bounds', '')
    if not bounds: 
        return None

    x1, y1, x2, y2 = map(int, sum((point.split(',') for point in bounds[1:-1].split('][')), []))
    width, height = str(x2 - x1), str(y2 - y1)
    res = [index, container.get('resource-id', ''), container.get('class', ''), width, height]
    
    return ' '.join(filter(None, res))

def xml2json(filepath):
    """Convert an XML file to a JSON structure."""
    tree = []
    array = []
    try:
        root = ET.parse(filepath).getroot()[0]
        add_element(tree, array, root, root.get('index', '0'))
        return {'tree': tree, 'array': array}
    except Exception as e:
        return f"Error: {e}"