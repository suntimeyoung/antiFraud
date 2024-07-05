import random
import shutil
import json
import re
import os

from bs4 import BeautifulSoup
from openai_api import GPT

# 获取一个网页中图片的最多数量
max_image_count = 15
# 图片的最大长度，一般过大的都是图片的编码
max_image_size = 100
# GPT的最大上下文窗口
max_gpt_window_size = 2500
# 测试样本数
max_testcase_count = 1
# 随机数种子，若为 None，则不设定
random_seed = 8827567
# 文件输入输出目录
input_path = 'E:/WORK/Files/input/'
output_path = 'E:/WORK/Files/output/'


def parse_html(file_path):
    """
    解析HTML文件并返回BeautifulSoup对象
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return BeautifulSoup(content, 'html.parser')


def list_files(directory):
    # 列出目录下的所有文件和文件夹
    all_files = os.listdir(directory)
    # 过滤出文件
    files = [f for f in all_files if os.path.isfile(os.path.join(directory, f))]
    return files


def copy_into_dir(file_list):
    # 遍历目录中的所有文件和文件夹
    for filename in os.listdir('./tmp'):
        file_path = os.path.join('./tmp', filename)
        try:
            # 检查文件路径是否为文件，如果是则删除
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    for filename in file_list:
        shutil.copy(input_path + filename, './tmp')


def is_valid_json(input_data):
    try:
        input_data = json.loads(input_data)
    except:
        return False

    # 检查输入是否为字典
    if not isinstance(input_data, dict):
        return False

    # 检查字典是否具有指定的键
    required_keys = ["characteristic_phrases", "fraud_tag", "web_type"]
    for key in required_keys:
        if key not in input_data:
            return False

    # 检查键 "characteristic_phrases" 的值是否为列表，且列表中的每个元素都是字符串
    if not isinstance(input_data["characteristic_phrases"], list):
        return False
    for phrase in input_data["characteristic_phrases"]:
        if not isinstance(phrase, str):
            return False

    # 检查键 "fraud_tag" 和 "web_type" 的值是否为字符串
    if not isinstance(input_data["fraud_tag"], str):
        return False
    if not isinstance(input_data["web_type"], str):
        return False

    return True


def get_website_text(soup):
    """
    从BeautifulSoup对象中提取并处理文本
    """
    text = soup.get_text().strip()
    return split_text_into_lines(text)


def split_text_into_lines(text):
    """
    将文本按行分割并过滤掉空行和仅包含数字的行
    """
    lines = re.split(r'[\n\t]', text)
    filtered_lines = [line.strip() for line in lines if line.strip() and not line.strip().isdigit()]
    return filtered_lines


def get_html_candidates(soup):
    """
    提取包含href或src属性的特定HTML标签
    """
    candidates = []
    tags = ['link', 'img']
    count = 1

    for tag in tags:
        elements = soup.find_all(tag)
        for element in elements:
            img_text = ''
            href = element.get('href')
            src = element.get('src')
            if href:
                img_text = f'<{tag} href="{href}">'
            elif src:
                img_text = f'<{tag} src="{src}">'

            # 处理.css样式文件
            if 0 < len(img_text) < max_image_size and re.search(r'\.css">$', img_text, re.IGNORECASE) is None:
                candidates.append(img_text)
                count += 1

            if count == max_image_count:
                return candidates
    return candidates


def extract_meta_information(soup):
    """
    提取HTML的meta信息，包括title、description和keywords
    """
    meta_info = []

    if soup.title:
        meta_info.append(f"{soup.title.string}</title>")

    description = soup.find('meta', attrs={'name': 'description'})
    if description and 'content' in description.attrs:
        meta_info.append(f"description: {description['content']}")

    keywords = soup.find('meta', attrs={'name': 'keywords'})
    if keywords and 'content' in keywords.attrs:
        meta_info.append(f"keywords: {keywords['content']}")

    return meta_info


def clean_strings(strings):
    """
    对输入的字符串列表进行处理，删除所有数字和连在一起的标点符号，同时删除空字符串
    """
    cleaned_strings = []
    for string in strings:
        # 删除所有数字
        string = re.sub(r'\d+', '', string)
        # 删除连在一起的标点符号
        string = re.sub(r'[^\w\s]+(?=[^\w\s])|(?<=[^\w\s])[^\w\s]+', '', string)
        # 删除首尾的标点符号
        string = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', string)
        # 删除多余的空格
        string = string.strip()
        # 仅添加非空字符串
        if string:
            cleaned_strings.append(string)
    return cleaned_strings


def random_drop(max_length, text_list):
    """
    从text_list中随机丢弃元素，直到其字符串表示形式的长度小于max_length。
    """
    while len(repr(text_list)) >= max_length and text_list:
        # 随机选择一个索引
        index_to_remove = random.randint(0, len(text_list) - 1)
        # 移除该索引的元素
        text_list.pop(index_to_remove)
    return text_list


def html_filter(file_path):
    """
    过滤HTML内容并返回处理后的信息列表
    """
    soup = parse_html(file_path)

    # 处理源代码，获得文本信息
    filtered_list = extract_meta_information(soup)
    filtered_list += random_drop(max_gpt_window_size - max_image_size * max_image_count, get_website_text(soup))
    # filtered_list += clean_strings(random_drop(max_gpt_window_size - max_image_size * max_image_count, get_website_text(soup)))
    filtered_list += get_html_candidates(soup)


    # 缩短列表长度至窗口长度以内
    pass

    return filtered_list


def handle_file_list(seed):
    gpt = GPT()
    filename_list = list_files(input_path)
    if seed is None:
        seed = random.randint(0, 1000000)
    print(f"random seed is: {seed}")
    random.seed(seed)
    test_file_list = random.sample(filename_list, max_testcase_count)
    for filename in test_file_list:
        print('-----------------------------------------')
        html_list = html_filter(input_path + filename)
        print(f"{filename}'s size = {len(repr(html_list))}")
        print(repr(html_list))
        # 向gpt发出询问
        check = False
        while check == False:
            # answer = gpt.query_api_sectional(repr(html_list))
            answer = gpt.query_api_single(repr(html_list))
            print(answer)
            check = is_valid_json(answer)
        # print(answer)
        # 输出到文件
        with open(output_path + filename + '.output', 'w', encoding='utf-8') as f:
            f.write(answer)
    copy_into_dir(test_file_list)


def main():
    handle_file_list(random_seed)


if __name__ == "__main__":
    main()
