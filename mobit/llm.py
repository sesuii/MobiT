import json
import re
import time

import openai

from .config import load_config
from mobit import prompts, file_utils, img_utils
from mobit.file_utils import read_json
from mobit.img_utils import print_with_color

configs = load_config()
client = openai.OpenAI(api_key=configs['OPENAI_API_KEY'], base_url=configs['OPENAI_API_BASE'])

def parse_response(response):
    if isinstance(response, dict):
        return response['choices'][0]['message']['content']
    else:
        return response.choices[0].message.content


def extract_json_from_rsp(response):
    """
    Extract JSON from the response text.
    """
    try:
        return json.loads(response[response.find('{'): response.rfind('}')+1])
    except (IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing JSON: {e}")
        return None

def ask_gpt(messages, model=configs['MODEL_NAME'], max_tokens=configs['MAX_TOKENS'], temperature=configs['TEMPERATURE'], attempts=3):
    for times in range(attempts):
        try:
            start = int(time.time())
            response = json.loads(client.chat.completions.create(model=model,
                                                      messages=messages,
                                                      max_tokens=max_tokens,
                                                      n=1,
                                                      stop=None,
                                                      temperature=temperature).model_dump_json())
            period = int(time.time()) - start
            input_cost = response['usage']['prompt_tokens'] * 0.15 / 1000000
            output_cost = response['usage']['completion_tokens'] * 0.06 / 1000000
            print_with_color(f'TIME: {period}s', 'yellow')
            print_with_color(f'INPUT_COST: {input_cost}$', 'yellow')
            print_with_color(f'OUTPUT_COST: {output_cost}$', 'yellow')
            return response
        except openai.OpenAIError as e:
            print(f"Attempt {times + 1} failed with error: {str(e)}")
            if times < 2:
                print(f"Take a 60*{times + 1} seconds break before the next attempt...")
                time.sleep(60 * (times + 1))
            else:
                print(f"All {attempts} attempts failed. Please try again later.")
                raise e
    return None


def ask_page(page_config):
    """
    Ask LLM to analyze a page.
    """
    img_encoded = f"data:image/jpeg;base64,{img_utils.encode_image(page_config['img_path'])}"
    json_tree = file_utils.read_json(page_config['json_path'])['tree']
    app_info = {
        'appActivity': page_config['appActivity'],
        'appPackage': page_config['appPackage'],
        'app_intro': read_json(configs['APP_INTRO_PATH'])['intro'],
    }

    def create_message(prompt, log: bool = False):
        img_path = page_config['img_path']
        json_path = page_config['json_path']
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "text",
                        "text": f"- xml:\t{json_tree if not log else json_path} \n\n - information:\t{app_info}\n\n",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": img_encoded if not log else img_path, "detail": "low"},
                    },
                ],
            }
        ]

    messages = {
        'page_segmentation': create_message(prompts.page_segmentation),
        'representative_ui_elements': create_message(prompts.representative_ui_elements),
    }
    messages_log = {
        'page_segmentation': create_message(prompts.page_segmentation, log=True),
        'representative_ui_elements': create_message(prompts.representative_ui_elements, log=True),
    }
    responses = {key: ask_gpt(msg) for key, msg in messages.items()}
    for key, msg in messages_log.items():
        file_utils.log([{
            "response": responses[key],
            "request": msg,
        }])
    responses = {key: extract_json_from_rsp(parse_response(response)) for key, response in responses.items()}
    return {**responses['page_segmentation'], **responses['representative_ui_elements']}

def ask_action(context):
    """
    Ask LLM for next action.
    """
    app_info = {
        'appActivity': context['appActivity'],
        'appPackage': context['appPackage'],
        'app_intro': read_json(configs['APP_INTRO_PATH'])['intro'],
    }
    def create_message(log: bool = False):
        img_path = context['img_path']
        json_path = context['json_path']

        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompts.next_action},
                    {"type": "text", "text": f"- Views_History: \t{context['steps']} \n\n"
                                             f"- Hierarchy: \t{file_utils.read_json(context['json_path']) if not log else json_path} \n\n"
                                             f"- App_Information: \t{app_info}\n\n"
                                             f"- the_Target_Area: \t{context['module']}\n\n"},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{img_utils.encode_image(context['img_path']) if not log else img_path}",
                                   "detail": "low"}},
                ],
            },
        ]
    messages = create_message()
    response = ask_gpt(messages)
    file_utils.log([{
        "response": response,
        "request": create_message(log=True)
    }])
    action = extract_json_from_rsp(parse_response(response))
    def determine_action(act):
        print(f'    ⚡️Current Action: {act}')
        if act == None or act == "FINISH":
            return ["FINISH"]
        act_name = act.split("(")[0]
        if act_name == "tap":
            area = re.findall(r"tap\((.*?)\)", act)[0]
            return {"type": "tap", "ele": {"index": area}}
        elif act_name == "text":
            input_str = re.findall(r"text\((.*?)\)", act)[0][1:-1]
            return {"type": "input", "msg": input_str}
        elif act_name == "long_press":
            area = re.findall(r"long_press\((.*?)\)", act)[0]
            return {"type": "long_press", "ele": {"index": area}}
        elif act_name == "swipe":
            params = re.findall(r"swipe\((.*?)\)", act)[0]
            area, swipe_dir, dist = params.split(",")
            swipe_dir = swipe_dir.strip()[1:-1]
            dist = dist.strip()[1:-1]
            return {"type": "swipe", "ele": {"index": area, "direction": swipe_dir, "distance": dist}}
        else:
            print_with_color(f'    🐛Unknown Action: {act}', 'red')
            return None
    return determine_action(action['Action'] if action and 'Action' in action else action)


def ask_fun_map(actions, func_logic_map, marked_image_path, concat_image_path):
    """
    Ask LLM to build functional map.
    """
    def create_message(log: bool = False):
        return [
        {
            "role": "user",
            "content": [
                    {
                    "type": "text",
                    "text": prompts.logic_graph_generation
                    },{
                    "type": "text",
                    "text": f"\
                        - actions:{actions}\n\
                        - fun_map:{func_logic_map} \n \
                            \n ",
                    },{
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_utils.encode_image(marked_image_path) if not log else marked_image_path}","detail": "low",},
                    }, {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_utils.encode_image(concat_image_path) if not log else concat_image_path}","detail": "low",},
                    },
            ]}]
    messages = create_message()
    response = ask_gpt(messages)
    file_utils.log([{
        "response": response,
        "request": create_message(log=True)
    }])
    response = extract_json_from_rsp(parse_response(response))
    return response

def ask_fun_path(logic_map):
    """
    Ask LLM to generate functional paths.

    This function uses the LLM to generate step-by-step functional paths
    based on the functional logic map.

    Args:
        logic_map: Functional logic map

    Returns:
        Dictionary with functional paths
    """
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompts.logic_path_generation},
            ],
        },{
            "role": "user",
            "content": [
                {"type": "text", "text": f"\
                        - fun_map:{logic_map} \n \
                            \n "},
            ]}]
    response = ask_gpt(messages)
    file_utils.log([{
        "response": response,
        "request": messages
    }])
    response = extract_json_from_rsp(parse_response(response))
    functional_logic_paths = response['functional_logic_paths']
    for path in functional_logic_paths:
        messages = [{
        "role": "user",
        "content": [
                {
                "type": "text",
                "text": prompts.step_desc_generation
                },{
                "type": "text",
                "text": f"\
                    - fun_map:{logic_map} \n \
                    - functional_logic_paths:{path}\n ",
                }
        ]}]
        rsp = ask_gpt(messages)
        file_utils.log([{
            "response": rsp,
            "request": messages
        }])
        path['step_desc'] = extract_json_from_rsp(parse_response(rsp))['steps']
    return functional_logic_paths


def ask_defect_detection(path_info, path_concat_img):
    """
    Ask LLM to detect defects.      
    """
    def create_message(log: bool = False):
        return [
        {
            "role": "user",
            "content": [
                    {
                    "type": "text",
                    "text": prompts.defect_detection
                    },{
                    "type": "text",
                    "text": f"\
                        - current logic path:{path_info} \n \
                            \n ",
                    },{
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_utils.encode_image(path_concat_img) if not log else path_concat_img}","detail": "low",},
                    }
            ]}]
    messages = create_message()
    response = ask_gpt(messages)
    file_utils.log([{
        "response": response,
        "request": create_message(log=True)
    }])
    response = extract_json_from_rsp(parse_response(response))
    return response['defects']