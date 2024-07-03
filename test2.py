def read_file_to_string(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content

file_path = 'systemMessage.txt'  # 请将your_file.txt替换为你的文件路径
file_content = read_file_to_string(file_path)
print(file_content)
