import base64
from typing import List, Optional, Tuple

import cv2
import pyshine as ps

from colorama import Fore, Style
from PIL import Image, ImageDraw, ImageFont

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def print_with_color(text: str, color=""):
    if color == "red":
        print(Fore.RED + text)
    elif color == "green":
        print(Fore.GREEN + text)
    elif color == "yellow":
        print(Fore.YELLOW + text)
    elif color == "blue":
        print(Fore.BLUE + text)
    elif color == "magenta":
        print(Fore.MAGENTA + text)
    elif color == "cyan":
        print(Fore.CYAN + text)
    elif color == "white":
        print(Fore.WHITE + text)
    elif color == "black":
        print(Fore.BLACK + text)
    else:
        print(text)
    print(Style.RESET_ALL)


def draw_bbox_multi(img_path, output_path, elem_list, record_mode=False, dark_mode=False):
    imgcv = cv2.imread(img_path)
    count = 1
    for elem in elem_list:
        try:
            top_left = elem.bbox[0]
            bottom_right = elem.bbox[1]
            left, top = top_left[0], top_left[1]
            right, bottom = bottom_right[0], bottom_right[1]
            label = str(count)
            if record_mode:
                if elem.attrib == "clickable":
                    color = (250, 0, 0)
                elif elem.attrib == "focusable":
                    color = (0, 0, 250)
                else:
                    color = (0, 250, 0)
                imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10, text_offset_y=(top + bottom) // 2 + 10,
                                    vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=color,
                                    text_RGB=(255, 250, 250), alpha=0.5)
            else:
                text_color = (10, 10, 10) if dark_mode else (255, 250, 250)
                bg_color = (255, 250, 250) if dark_mode else (10, 10, 10)
                imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10, text_offset_y=(top + bottom) // 2 + 10,
                                    vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=bg_color,
                                    text_RGB=text_color, alpha=0.5)
        except Exception as e:
            print_with_color(f"ERROR: An exception occurs while labeling the image\n{e}", "red")
        count += 1
    cv2.imwrite(output_path, imgcv)
    return imgcv


def draw_boxes_with_labels(
    image_path,
    boxes,
    ids,
    source_page_id,
    output_path,
    box_color="red",
    box_width=3,
    bg_color=(128, 128, 128, 128),  # 半透明灰色 (R,G,B,A)
    text_color=(255, 255, 255, 255),# 白色文字，不透明
    font_size=32,
    filename_font_size=32,          # 可与上方 font_size 不同
    bottom_margin=20                # 文本和下方的留白
):
    """
    在图像上画出多个矩形框并标注序号（带半透明背景），
    然后扩展画布，在下方居中放置图片名。
    
    :param image_path:  原始图片路径
    :param boxes:       矩形框列表，每个框 [x1,y1,x2,y2]
    :param ids:         每个矩形对应id，用于标注
    :param output_path: 输出图片路径
    :param box_color:   矩形框颜色
    :param box_width:   矩形边框宽度
    :param bg_color:    序号文字背景颜色(含Alpha)
    :param text_color:  文字颜色(含Alpha)
    :param font_size:   矩形框序号字体大小
    :param filename_font_size: 底部文件名字体大小
    :param bottom_margin: 文件名与下边缘的额外留白
    """
    # 1) 打开原图(RGBA)
    original_img = Image.open(image_path).convert("RGBA")

    # 2) 在原图上画矩形框(不扩展画布，保持原尺寸)
    draw_main = ImageDraw.Draw(original_img)
    for box in boxes:
        x1, y1, x2, y2 = box
        draw_main.rectangle([x1, y1, x2, y2], outline=box_color, width=box_width)

    # 3) 在一个临时 overlay 上绘制半透明背景+文字(序号)
    overlay = Image.new("RGBA", original_img.size, (255, 255, 255, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    font = ImageFont.truetype('resources/Roboto-Regular.ttf', font_size)

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        label_text = f"{i}-p{ids[i]}"  # "0-Pxxx"

        text_bbox = draw_overlay.textbbox((0,0), label_text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        # 放在框左上角之上
        text_x = x1
        text_y = y1 - (text_h + 10)
        # 防止越界
        if text_y < 0:
            text_y = y1

        # 半透明背景矩形
        padding = 4
        bg_left   = text_x - padding
        bg_top    = text_y - padding
        bg_right  = text_x + text_w + padding
        bg_bottom = text_y + text_h + padding*2
        draw_overlay.rectangle([bg_left, bg_top, bg_right, bg_bottom], fill=bg_color)
        draw_overlay.text((text_x, text_y), label_text, font=font, fill=text_color)

    # 4) 合成 overlay + 原图
    final_img = Image.alpha_composite(original_img, overlay)

    # ============= 新增：扩展画布，在下方写文件名 =============
    
    # 4.1 先测量文件名要占多高
    filename = "source_page_id : "+ str(source_page_id)
    font_filename = ImageFont.truetype('resources/Roboto-Regular.ttf', filename_font_size)
    dummy_draw = ImageDraw.Draw(final_img)  # 用于测量宽高
    name_bbox = dummy_draw.textbbox((0,0), filename, font=font_filename)
    name_w = name_bbox[2] - name_bbox[0]
    name_h = name_bbox[3] - name_bbox[1]

    # 需要在下方新增多少高度
    extra_height = name_h + bottom_margin*2  # 给一些上下留白

    # 4.2 创建一张新的图像，高度 = 原图高度 + extra_height
    new_width = final_img.width
    new_height = final_img.height + extra_height
    extended_img = Image.new("RGBA", (new_width, new_height), (255,255,255,0))

    # 4.3 将final_img贴到新图顶部
    extended_img.paste(final_img, (0, 0))

    # 4.4 在新图底部居中写文件名(可加半透明背景)
    draw_extended = ImageDraw.Draw(extended_img)

    # 计算居中坐标
    text_x = (new_width - name_w)//2
    text_y = final_img.height + (bottom_margin//2)

    # # 可在文字后画个半透明背景
    # padding_bg = 8
    # bg_left   = text_x - padding_bg
    # bg_top    = text_y - padding_bg
    # bg_right  = text_x + name_w + padding_bg
    # bg_bottom = text_y + name_h + padding_bg

    # 背景颜色可复用 bg_color, 也可自定义
    # draw_extended.rectangle([bg_left, bg_top, bg_right, bg_bottom], fill=bg_color)

    draw_extended.text((text_x, text_y), filename, font=font_filename, fill=(0, 0, 0, 0))

    # 5) convert to RGB 并保存
    out_final = extended_img.convert("RGB")
    out_final.save(output_path)
    print(f"Done. Saved to {output_path}")

    
def concat_images_horizontally(image_paths, ids, output_path, gap=10, font_size=40, stage_idx=2):
    """
    将多张图片水平拼接（从左到右），在图片之间留一定间隔，
    并在每张图片下方标注图片文件名。
    
    :param image_paths: 图片路径列表
    :param output_path: 拼接后保存路径
    :param gap: 图片之间的水平间距（单位：像素）
    :param font_size: 文件名文字大小
    :return: 拼接后的 PIL Image 对象
    """
    # 1) 打开并读取所有图像
    images = [Image.open(p).convert("RGB") for p in image_paths]

    # 2) 计算每张图像的大小，统计总宽度、最大高度
    widths, heights = zip(*(img.size for img in images))
    total_width = sum(widths) + gap * (len(images) - 1)  # 加上 (len-1) 个间隔
    max_height = max(heights)

    # 3) 预估文字区域高度
    #    使用 TrueType 字体，如果不需要中文可用任何 TTF 文件；此处示例使用系统常见字体
    # font = ImageFont.load_default()
    # 或者自定义字体路径：
    font = ImageFont.truetype('resources/Roboto-Regular.ttf', font_size)
    # 计算单行文字大约高度
    img = Image.new("RGB", (200,200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0,0), "test_img", font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    # 实际需要的文字高度可稍加余量
    label_height = text_h + 20  # 给一些额外空白

    # 4) 新建合成图像：高度为 max_height + label_height
    new_im = Image.new("RGB", (total_width, max_height + label_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(new_im)

    # 5) 依次将每张图片拼接到 new_im 中，并在下方写上文件名
    x_offset = 0
    i = 0
    for path, img in zip(image_paths, images):
        # 5.1) 把图粘贴到 (x_offset, 0)
        new_im.paste(img, (x_offset, 0))
        
        # 5.2) 在图片下方写文件名
        if stage_idx == 2:
            filename = f"action_id : {str(i)}    ,   target_page_id : {str(ids[i])}"  # 获取最后的文件名部分
        else:
            filename = f'current_page_id : {str(ids[i])}'
        text_x = x_offset
        text_y = max_height + 2  # 在图片底部稍微留一点距离
        draw.text((text_x, text_y), filename, fill=(0,0,0), font=font)

        # 5.3) 累加 offset，给下张图预留位置 + gap
        x_offset += img.width + gap
        i+=1

    # 6) 保存并返回结果图
    new_im.save(output_path)
    print(f"拼接完成: {output_path}")
    return new_im