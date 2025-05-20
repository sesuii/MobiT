import os
import json
from datetime import datetime

from .config import load_config

configs = load_config()
app_package = configs['APP_PACKAGE']
exec_round = configs['ROUND']
base_dir = configs['SAVED_BASE_DIR']

def get_timestamp():
    """
    Generate a timestamp and create paths for saving files.

    Returns:
        Dictionary with paths for XML, image, and JSON files
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = os.path.join(base_dir, f'{app_package}_{exec_round}')
    # Create paths
    return {
        'timestamp': timestamp,
        'save_dir': os.path.join(output_dir, 'assets'),
        'xml_path': os.path.join(output_dir, f'assets/{timestamp}.xml'),
        'img_path': os.path.join(output_dir, f'assets/{timestamp}.png'),
        'img_labeled_path': os.path.join(output_dir, f'assets/{timestamp}_labeled.png'),
        'json_path': os.path.join(output_dir, f'assets/{timestamp}.json'),
        'element_path': os.path.join(output_dir, f'assets/{timestamp}-element.json')
    }


def init_output():
    """
    Initialize output directory and files.

    Args:
        output_dir: Base output directory
    """
    # Create app-specific directory
    app_dir = os.path.join(base_dir, f'{app_package}_{exec_round}')
    os.makedirs(app_dir, exist_ok=True)
    # Create assets directory
    assets_dir = os.path.join(app_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    return read_output(app_dir)


def read_output(app_dir: str=None):
    """
    Read pages and links from output files.

    Returns:
        Tuple containing (pages, links)
    """
    if app_dir is None:
        app_dir = os.path.join(base_dir, f'{app_package}_{exec_round}')
    pages_path = os.path.join(app_dir, configs['PAGES_JSON_PATH'])
    transitions_path = os.path.join(app_dir, configs['TRANSITIONS_GRAPH_PATH'])
    logic_path = os.path.join(app_dir, configs['FUNC_LOGIC_GRAPH_PATH'])
    chat_history_path = os.path.join(app_dir, configs['CHAT_HISTORY_PATH'])
    defects_path = os.path.join(app_dir, configs['DEFECTS_PATH'])
    def read_or_create_json(path, default):
        """
        Read JSON data from a file or create an empty structure if the file doesn't exist.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, 'r', encoding='utf-8') as fi:
                return json.load(fi)
        except (json.JSONDecodeError, FileNotFoundError):
            with open(path, 'w', encoding='utf-8') as fi:
                json.dump(default, fi, indent=2)
            return default

    # Initialize empty data structures
    pages = read_or_create_json(pages_path, default=[])
    links = read_or_create_json(transitions_path, default=[])
    logic = read_or_create_json(logic_path, default={})
    chat_history = read_or_create_json(chat_history_path, default=[])
    defects = read_or_create_json(defects_path, default=[])

    return pages, links, logic, chat_history


def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_json(path: str):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def write_output(pages, links):
    """
    Write pages and links to output files.

    """
    app_dir = os.path.join(base_dir, f'{app_package}_{exec_round}')
    pages_path = os.path.join(app_dir, configs['PAGES_JSON_PATH'])
    transitions_path = os.path.join(app_dir, configs['TRANSITIONS_GRAPH_PATH'])
    write_json(pages_path, pages)
    write_json(transitions_path, links)


def write_text(path: str, text: str):
    """
    Write text to a file.

    Args:
        path: Path to the output file
        text: Text to write
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Write text
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def log(data, log_path: str=None):
    if not log_path:
        log_path = os.path.join(base_dir, f'{app_package}_{exec_round}', configs['CHAT_HISTORY_PATH'])
    with open(log_path, 'r', encoding='utf-8') as f:
        ori_data = json.load(f)
    if isinstance(data, list):
        ori_data.extend(data)
    else:
        ori_data.append(data)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(ori_data, f, indent=2)
