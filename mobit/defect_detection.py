"""
Defect Detection Stage - Analyzes functional logic paths to detect potential defects.

This module implements the third stage of the OriChat workflow, which analyzes
the functional logic paths and page transitions to identify potential defects
in the Android application.
"""

import os

from mobit import file_utils, img_utils, llm, config
configs = config.load_config()
base_dir = configs['SAVED_BASE_DIR']
app_package = configs['APP_PACKAGE']
exec_round = configs['ROUND']
app_dir = os.path.join(base_dir, f'{app_package}_{exec_round}')
concat_image_dir = os.path.join(app_dir, 'logic_paths')
os.makedirs(concat_image_dir, exist_ok=True)


def run():
    """
    Stage 3 - Defect Detection
    """
    pages, links, logic, chat_history = file_utils.read_output()
    logic_paths = logic.get('functional_logic_paths', [])
    defects = []
    for path in logic_paths:
        path_info = {
            'path_id': path['path_id'],
            'path_description': path['path_description'],
            'expected_result': path['expected_result'],
            'page_ids': [],
            'step_desc': []
        }
        filter_function_ids = []
        images = []
        for step in path['step_desc']:
            if step['function_id'] in filter_function_ids:
                continue
            filter_function_ids.append(step['function_id'])
            for node in logic['function_nodes'][step['function_id']]['related_pages']:
                node['page_id'] = int(node['page_id'])
                images.append(pages[node['page_id']]['page_config']['img_path'])
                path_info['page_ids'].append(node['page_id'])
            path_info['step_desc'].append(step)
        path_concat_img_path = os.path.join(concat_image_dir, f'path_{path['path_id']}_concat.jpg')
        path_concat_img = img_utils.concat_images_horizontally(
            image_paths=images,
            ids=path_info['page_ids'],
            output_path=path_concat_img_path,
            stage_idx=3
        )
        path_info['defects'] = llm.ask_defect_detection(path_info, path_concat_img_path)
        path_info['path_concat_img'] = path_concat_img_path
        defects.append(path_info)
    defects_path = os.path.join(app_dir, configs['DEFECTS_PATH'])
    file_utils.write_json(defects_path, defects)
    img_utils.print_with_color(f"✨ Stage 3 - Defect Detection completed and saved to {defects_path}", "green")
    