import random
import shutil
import json
import time
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
max_testcase_count = 10
# 随机数种子，若为 -1，则不设定，自动生成，若为None，顺序执行
random_seed = 2139
# 文件输入输出目录
input_path = 'E:/WORK/Files/input/'
# tag内容
fraud_tag = ['涉诈', '不涉诈', '无可提取特征']
web_tag = ['赌博诈骗', '色情诈骗', '防封跳转页', '黑产交易平台', '刷信誉', '仿冒京东商城',
           '数字资产交易平台', '客服平台', '聊天室', 'APP下载页', '仿冒淘宝', '数字货币或挖矿平台',
           '虚假金融交易平台', '仿冒幸运领奖', '仿冒公安部', 'VPN', '仿冒航空公司', '发卡平台',
           '第四方支付平台', '虚假购物平台', 'NFT数字收藏品交易平台', '仿冒政府部门', '色情直播',
           '接码平台', '仿冒网游交易门户', '色情交友', '色情赌博广告页', '付费VPN', '仿冒银联支付',
           '彩票诈骗', '仿冒QQ安全中心', '应用分发平台', '仿冒微信安全中心', '虚假借贷', '六合彩论坛', '免费VPN',
           '']


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


def is_valid_json(input_data, html_list):
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
    if isinstance(input_data["fraud_tag"], str):
        if input_data["fraud_tag"] not in fraud_tag:
            print(f'Error: {input_data["fraud_tag"]} not in fraud_tag')
            return False
    else:
        return False
    if isinstance(input_data["web_type"], str):
        if input_data["web_type"] not in web_tag:
            print(f'Error: {input_data["web_type"]} not in web_tag')
            return False
    else:
        return False

    for phrase in input_data["characteristic_phrases"]:
        check = False
        for origin_text in html_list:
            if phrase in origin_text:
                check = True
        if not check:
            print(f'Error: {phrase} not in html_list')
            return False

    return True


def get_website_text(soup):
    """
    从BeautifulSoup对象中提取并处理文本
    """
    text = soup.get_text(separator="<\n").strip()
    return split_text_into_lines(text)


def split_text_into_lines(text):
    """
    将文本按行分割并过滤掉空行和仅包含数字的行
    """
    lines = re.split(r'[\n\t]', text)
    cleaned_lines = []
    for line in lines:
        clean_line = re.sub(r'^<', '', line.strip()).strip()
        if clean_line and not line.isdigit():
            cleaned_lines.append(clean_line)
    return cleaned_lines


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
    filtered_list += get_html_candidates(soup)

    # 缩短列表长度至窗口长度以内
    pass

    return filtered_list


def format_answer(answer, html_list):
    answer = json.loads(answer)
    format_phrase = []
    for phrase in answer["characteristic_phrases"]:
        if phrase == '':
            continue
        format_phrase.append(phrase)
        for origin_text in html_list:
            if phrase + '<' in origin_text:
                format_phrase[-1] += '<'
                break
    answer["characteristic_phrases"] = format_phrase
    return json.dumps(answer, ensure_ascii=False)


def handle_file_list(seed):
    gpt = GPT()
    filename_list = list_files(input_path)
    if seed is None:
        test_file_list = filename_list[:max_testcase_count]
    else:
        if seed == -1:
            seed = random.randint(0, 1000000)
        print(f"random seed is: {seed}")
        random.seed(seed)
        test_file_list = random.sample(filename_list, max_testcase_count)
    for filename in test_file_list:
        print('-----------------------------------------')
        html_list = html_filter(input_path + filename)
        # print(f"{filename}'s size = {len(repr(html_list))}")
        # print(repr(html_list))
        # 向gpt发出询问
        check = False
        answer = ''
        while check == False:
            # answer = gpt.query_api_sectional(repr(html_list))
            answer = gpt.query_api_single(repr(html_list))
            # print(answer)
            check = is_valid_json(answer, html_list)
        answer = format_answer(answer, html_list)
        print(answer)
        # 输出到文件
        # with open(output_path + filename + '.output', 'w', encoding='utf-8') as f:
        #     f.write(answer)
    copy_into_dir(test_file_list)
    print('=====================================================')
    print(f"Total_tokens = {gpt.total_tokens}")
    print(f"Speed = {(time.time() - gpt.total_time) / gpt.total_rounds} s/round")
    print('=====================================================')


def main():
    handle_file_list(random_seed)


if __name__ == "__main__":
    main()
