"""
Logic Graph Stage - Builds the functional logic graph for an Android application.

This module implements the second stage of the OriChat workflow, which analyzes
the page relationship graph and builds a functional logic graph representing
the application's business logic and user flows.
"""
import re
import os

from mobit import file_utils, img_utils, llm, config
configs = config.load_config()
base_dir = configs['SAVED_BASE_DIR']
app_package = configs['APP_PACKAGE']
exec_round = configs['ROUND']
app_dir = os.path.join(base_dir, f'{app_package}_{exec_round}')
concat_image_dir = os.path.join(app_dir, 'page_out')
os.makedirs(concat_image_dir, exist_ok=True)

def build_transition_matrix(pages, links):
    """
    构建状态转换矩阵，表示页面之间的转换关系。  
    """
    n = len(pages)
    matrix = [[[] for _ in range(n)] for _ in range(n)]

    # Process each link
    for link in links:
        for step in link:
            if step['to'] == 'out_of_app':
                continue
            step_ele = step.get('ele', {})
            info = {
                'type': step.get('type', 'unknown'),
                **step_ele,
                'assets': step.get('assets', {})
            }
            if all(info != act for act in matrix[step['from']][step['to']]):
                matrix[step['from']][step['to']].append(info)
            if not matrix[step['from']][step['to']]:
                matrix[step['from']][step['to']].append(info)
    return matrix

def extract_out_links(matrix, pages, row_index):
    """
    提取页面的所有出链信息，并处理截图。
    """
    row = matrix[row_index]
    start_img = pages[row_index]['page_config']['img_path']
    boxes = []
    end_ids = []
    images = []

    page_infos = [{
        "pageId": row_index,
        "page_overview": pages[row_index]['page_overview'],
    }]

    action_infos = []

    # Process each cell in the row (transitions to other pages)
    for j, cells in enumerate(row):
        # Add target page info
        page_infos.append({
            "pageId": j,
            "page_overview": pages[j]['page_overview'],
        })

        # Process each action in the cell
        for cell in cells:
            # Extract text information from the action
            result_str = []
            for k, v in cell.items():
                if k in ('text', 'class', 'resource-id', 'content-desc'):
                    result_str.append(f"{v}")
                    
            # 安全地获取bounds信息
            if 'bounds' in cell:
                nums_str = re.findall(r"\d+", cell['bounds'])
                boxes.append(list(map(int, nums_str)))
                end_ids.append(str(j))
                # Add action info
                action_infos.append({
                    'source_page_id': str(row_index),
                    'target_page_id': str(j),
                    'action_id': len(action_infos),
                    'type': cell.get('type', 'unknown'),
                    'content': ' '.join(result_str),
                })
                
                # Add image path for visualization
                if 'assets' in cell and 'img_path' in cell['assets']:
                    images.append(cell['assets']['img_path'])

    if end_ids:
        # Draw boxes on source page image
        img_utils.draw_boxes_with_labels(
            image_path=start_img,
            boxes=boxes,
            ids=end_ids,
            output_path=f'{concat_image_dir}/{row_index}_marked.jpg',
            source_page_id=row_index
        )

        # Concatenate target page images
        if images:
            img_utils.concat_images_horizontally(
                image_paths=images,
                ids=end_ids,
                output_path=f'{concat_image_dir}/{row_index}_concat.jpg',
            )

    return action_infos, page_infos

def run():
    """
    Stage 2 - Logic Graph / Paths / Test Paths
    """
    pages, links, logic, chat_history = file_utils.read_output()
    matrix = build_transition_matrix(pages, links)
    action_infos = []
    fun_logic_map = {}
    for idx in range(len(pages)):
        page_actions, page_info = extract_out_links(matrix, pages, idx)
        if page_actions:
            action_infos.extend(page_actions)
            fun_logic_map.update(llm.ask_fun_map(
                page_actions,
                fun_logic_map,
                marked_image_path=f'{concat_image_dir}/{idx}_marked.jpg',
                concat_image_path=f'{concat_image_dir}/{idx}_concat.jpg'
            ))

    logic_path = os.path.join(app_dir, configs['FUNC_LOGIC_GRAPH_PATH'])
    
    # 保存功能逻辑图
    file_utils.write_json(logic_path, fun_logic_map)
    
    # 生成功能路径
    paths = llm.ask_fun_path(fun_logic_map)
    
    # 创建新的字典来存储最终结果
    final_result = {
        **fun_logic_map,
        'functional_logic_paths': paths
    }
    
    # 保存最终结果
    file_utils.write_json(logic_path, final_result)

    img_utils.print_with_color(f"✨ Stage 2 - Logic Graph completed and saved to {logic_path}", "green")