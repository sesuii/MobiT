import time
from .and_controller import list_all_devices, AndroidController
from .config import load_config
from mobit import file_utils, llm, xml_parser
from .img_utils import print_with_color

configs = load_config()
app_package = configs['APP_PACKAGE']
device = configs['CURRENT_DEVICE']
device_list = list_all_devices()
if device and device in device_list:
    and_controller = AndroidController(device)
if not device_list:
    print_with_color("🚨ERROR: No devices found", "red")
and_controller = AndroidController(device_list[0])

def initialize_pages(pages):
    act = exec_action()
    appinfo=act['appinfo']
    assets =act['assets']
    add_current_page(pages, appinfo, assets)

def re_launch_app():
    """
    Relaunch the app to ensure a clean state.
    """
    and_controller.stop_app()
    and_controller.start_app()
    time.sleep(3)

def exec_action(action=None, json_path=None):
    ret = {}
    print(action)
    if not action:
        re_launch_app()
    elif action == 'FINISH':
        return
    elif 'type' in action and action['type'] == 'tap':
        node = xml_parser.find_node(json_path, action['ele']['index'])
        if not node: return None
        # Extract bounds and calculate tap coordinates
        bounds = node['bounds'][1:-1].split("][")
        left, top = map(int, bounds[0].split(","))
        right, bottom = map(int, bounds[1].split(","))
        center_x, center_y = (left + right) // 2, (top + bottom) // 2
        and_controller.tap(center_x, center_y)
        time.sleep(3)
        ret = {
            **ret,
            **action,
            'type': 'tap',
            'ele': node,
        }
    elif 'type' in action and action['type'] == 'input':
        and_controller.text(action['msg'])
        time.sleep(3)
        ret = {
            **ret,
            **action,
            'type': 'input',
        }
    elif 'type' in action and action['type'] == 'long_press':
        node = xml_parser.find_node(json_path, action['ele']['index'])
        if not node: return None
        # Extract bounds and calculate tap coordinates
        bounds = node['bounds'][1:-1].split("][")
        left, top = map(int, bounds[0].split(","))
        right, bottom = map(int, bounds[1].split(","))
        center_x, center_y = (left + right) // 2, (top + bottom) // 2
        and_controller.long_press(center_x, center_y)
        time.sleep(3)
        ret = {
            **ret,
            **action,
            'type': 'long_press',
        }
    elif 'type' in action and action['type'] == 'swipe':
        node = xml_parser.find_node(json_path, action['ele']['index'])
        if not node: return None
        # Extract bounds and calculate tap coordinates
        bounds = node['bounds'][1:-1].split("][")
        left, top = map(int, bounds[0].split(","))
        right, bottom = map(int, bounds[1].split(","))
        center_x, center_y = (left + right) // 2, (top + bottom) // 2
        and_controller.swipe(center_x, center_y, action['ele']['direction'], action['ele']['distance'])
        time.sleep(3)
        ret = {
            **ret,
            **action,
            'type': 'swipe',
        }
    appinfo, assets = save_page_state()
    return {
        **ret,
        'appinfo': appinfo,
        'assets': assets
    }

def save_page_state():
    assets = file_utils.get_timestamp()
    app_info = and_controller.get_info()
    # Capture UI state
    and_controller.get_xml(assets['xml_path'])
    and_controller.get_screenshot(assets['img_path'])
    # TODO - Label the screenshot
    # Parse XML to JSON and save
    file_utils.write_json(
        assets['json_path'],
        xml_parser.xml2json(assets['xml_path'])
    )

    return app_info, assets

def add_current_page(pages, appinfo, assets):
    """
    Parse the current page and add it to the pages list.
    """
    # Organize page configuration data
    page_config = {
        'xml_path': assets['xml_path'],
        'img_path': assets['img_path'],
        'json_path': assets['json_path'],
        'appActivity': appinfo[1],
        'appPackage': appinfo[0],
    }

    # Use LLM to analyze the page
    ret = llm.ask_page(page_config)
    # Process functional modules
    for index, module in enumerate(ret['functional_modules']):
        module['index'] = index
        module['isFinished'] = False
        module['todoList'] = []
        if module['test_plan']['type'] == 'Sequential Click':
            module['todoList'].extend(module['interactive_elements'])
        elif module['test_plan']['type'] == 'Random Click':
            module['todoList'].append(module['interactive_elements'][0])
        else:
            module['todoList'].append('others')
    for category, elements in ret['representative_ui_elements'].items():
        eles = []
        for idx in elements:
            node = xml_parser.find_node(page_config['json_path'], idx)
            eles.append(node)
        ret['representative_ui_elements'][category] = eles

    # Create the page object
    current_page = {
        'index': len(pages),
        'isFinished': False,
        'page_config': page_config,
        'out_edges': [],  # Outgoing edges: current page → other pages
        'in_edges': [],  # Incoming edges: other pages → current page
        **ret
    }

    # Add to pages list
    pages.append(current_page)
    return current_page


def exec_steps(steps, pages=None):
    """
    Execute a sequence of steps to reach a specific page.

    Args:
        steps: List of actions to execute
        pages: List of pages (needed to find JSON paths)

    Returns:
        Result of the last action
    """
    re_launch_app()
    ret = None
    for step in steps:
        ret = exec_action(step, pages[step['from']]['page_config']['json_path'])
    return ret




def find_same_page(pages, current_page):
    """
    Find if the current page matches any existing page.

    Args:
        pages: List of existing pages
        current_page: Current page information

    Returns:
        Matching page object or -1 if no match found
    """
    for page in pages:
        results = []
        match_results = []

        # Check if activity matches
        if page['page_config']['appActivity'] == current_page['appinfo'][1]:
            # Check representative UI elements
            for category, elements in page['representative_ui_elements'].items():
                for element in elements:
                    node = xml_parser.find_node(current_page['assets']['json_path'], element['index'])
                    if node and matches_node(node, element):
                        match_results.append(node)
                    results.append(node)
            if len(results) == len(match_results):
                return page
    return -1


def matches_node(node, flag):
    """
    Check if a node matches the specified attributes.
    """
    # List of attributes to check
    attributes = ['resource-id', 'class', 'text', 'content', 'content-desc', 'index']

    # Check all attributes in the flag
    for attr in attributes:
        if attr in flag and node.get(attr) != flag[attr]:
            return False

    return True

def convert_actions_to_string_array(actions):
    """
    Convert action objects to string descriptions.
    """
    def assemble_description(action):
        """Helper function to assemble action description."""
        letter = action.get("msg", "")
        if not letter:
            element = action.get('ele', {})
            attributes = ['text', 'resource-id', 'class', 'content-desc']
            letter = ' '.join(element.get(attr, '') for attr in attributes if element.get(attr))
        return f"{action.get('type')}({letter})"

    return [assemble_description(action) for action in actions]




def test_module(pages, links, page_index, module_index):
    """
    Test a functional module and record page transitions.

    Args:
        pages: List of pages
        links: List of transition links
        page_index: Index of the page containing the module
        module_index: Index of the module to test
    """
    page = pages[page_index]
    module = page['functional_modules'][module_index]
    todo_list = module['todoList']

    # Get steps to reach this page
    steps = []
    if page['in_edges']:
        # Use the first incoming edge
        steps.extend(links[page['in_edges'][0]])
    act = exec_steps(steps, pages)
    count = 0
    interaction = []

    while count < 10:
        # Check termination conditions
        if not todo_list:
            module['isFinished'] = True
            return
        count += 1
        # Handle different test plan types
        if module['test_plan']['type'] == 'Other':
            # Use LLM to determine next action
            gpt_act = llm.ask_action({
                **act['assets'],
                'appActivity': act['appinfo'][1],
                'appPackage': act['appinfo'][0],
                'module': {
                    'module_name': module['module_name'],
                    'bounds': module['bounds'],
                    'interactive_elements': module['interactive_elements'],
                    'test_plan': module['test_plan'],
                },
                'steps': convert_actions_to_string_array(steps + interaction),
            })

            # Check if testing is complete
            if gpt_act == 'FINISH':
                module['isFinished'] = True
                return
            # Execute the suggested action
            act = exec_action(gpt_act, act['assets']['json_path'])
        else:
            # Execute predefined action (tap on element)
            act = exec_action(
                {"type": 'tap', 'ele': {'index': todo_list[0]}},
                page['page_config']['json_path']
            )
            # Handle failed action
            if not act:
                todo_list.pop(0)
                return
        if act == None or act == "FINISH":
            module['isFinished'] = True
            return
        # Record source page
        act['from'] = page['index']
        # Add to interaction history
        interaction.append(act)
        # Check if app exited
        if not act['appinfo']:
            todo_list.pop(0)
            act['to'] = "out_of_app"
            link = steps + interaction
            page['out_edges'].append(len(links))
            links.append(link)
            module['isFinished'] = True
            return

        # Check if we're on a known page
        to_page = find_same_page(pages, {'appinfo': act['appinfo'], 'assets': act['assets']})
        link_idx = len(links)
        link = steps + interaction

        if to_page == -1:
            # New page discovered
            current_page = add_current_page(pages, act['appinfo'], act['assets'])
            act['to'] = current_page['index']
            page['out_edges'].append(link_idx)
            current_page['in_edges'].append(link_idx)
            links.append(link)
        elif to_page['index'] != page['index']:
            # Transition to existing page
            act['to'] = to_page['index']
            page['out_edges'].append(link_idx)
            to_page['in_edges'].append(link_idx)
            links.append(link)
        else:
            # Self-loop (same page)
            act['to'] = page['index']
        if module['test_plan']['type'] != 'Other':
            todo_list.pop(0)


def run():
    """
    Stage 1: Initialize and build the page relationship graph.
    """
    # Initialize output directory and files
    pages, links, logic, chat_history = file_utils.init_output()

    # If pages data is empty, add the initial page
    if len(pages) == 0:
        print_with_color("🆕 ├── Initializing pages...", "yellow")
        initialize_pages(pages)
    file_utils.write_output(pages, links)
    # Main exploration loop
    while not all(page.get('isFinished', True) for page in pages):
        # Find an unfinished page
        for page in pages:
            if page.get('isFinished'):
                continue
                # Check if all modules in the page are finished
            print_with_color(f"➕ ├── Exploring page {page['index']}...", "yellow")
            if all(module.get('isFinished', True) for module in page['functional_modules']):
                # Mark page as finished and save
                page['isFinished'] = True
                file_utils.write_output(pages, links)
                # Find an unfinished module
                break
            for module in page['functional_modules']:
                if module.get('isFinished'):
                    continue
                print_with_color(f"    ➕ ├── Testing module {module['index']}...", "yellow")
                # Test the module
                test_module(pages, links, page['index'], module['index'])
                file_utils.write_output(pages, links)
            break
    print_with_color(f'✨First Stage COMPLETED: All pages in {app_package} have been tested.', 'cyan')