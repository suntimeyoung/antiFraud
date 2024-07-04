import socket
import json

# 改系统消息


# GPT参数配置信息
body_dict = {}
server_ip = '192.168.75.198'
server_port = 3002

# 修改gpt设置参数
body_dict['options'] = {}
body_dict['temperature'] = 0.9
body_dict['top_p'] = 0.8
systemMessage_filepath = ['systemMessage/systemMessage1.txt','systemMessage/systemMessage2.txt','systemMessage/systemMessage3.txt']

def read_file_to_string(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content


def is_valid_json(input_data):
    try:
        input_data = json.loads(input_data)
        # print(input_data)
    except:
        return False

    # 检查输入是否为字典
    if not isinstance(input_data, dict):
        return False

    # 检查字典是否具有指定的键
    required_keys = ["characteristic_phrases", "fraud_tag", "fraud_type"]
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
    if not isinstance(input_data["fraud_type"], str):
        return False

    return True

def create_request():
    body = json.dumps(body_dict, ensure_ascii=False)
    content_length = len(body.encode('utf-8'))

    request_line = "POST /api/chat-process HTTP/1.1\r\n"
    headers = (
        f"Host: {server_ip}:{server_port}\r\n"
        "Connection: keep-alive\r\n"  # Changed to keep-alive for persistent connection
        f"Content-Length: {content_length}\r\n"
        "Accept: application/json, text/plain, */*\r\n"
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0\r\n"
        "Content-Type: application/json\r\n"
        "Origin: http://192.168.75.198:3002\r\n"
        "Referer: http://192.168.75.198:3002/\r\n"
        "Accept-Encoding: gzip, deflate\r\n"
        "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6\r\n"
    )
    return f"{request_line}{headers}\r\n{body}"

def receive_full_response(sock):
    response = b""
    while True:
        part = sock.recv(4096)
        if not part:
            break
        response += part
        if b'0\r\n\r\n' in response:
            break
    return response

def parse_chunked_response(response):
    header, body = response.split(b"\r\n\r\n", 1)
    chunk = b''
    while body:
        chunk_size_str, body = body.split(b"\r\n", 1)
        chunk_size = int(chunk_size_str, 16)
        if chunk_size == 0:
            break
        chunk, body = body[:chunk_size], body[chunk_size+2:]  # +2 to remove \r\n after chunk
    json_chunk = json.loads(chunk.decode('utf-8'))
    return header.decode('utf-8'), json_chunk

def query_gpt_api(user_prompts):
    # 读取系统消息
    systemMessage = []
    for path in systemMessage_filepath:
        systemMessage.append(read_file_to_string(path))
    # print(systemMessage)
    # 创建socket对象
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接服务器
        client_socket.connect((server_ip, server_port))

        responses = 'error'
        parent_message_id = None

        if isinstance(user_prompts, str):
            user_prompts = [user_prompts]

        for i,user_prompt in enumerate(user_prompts):
            # print(i)
            body_dict['systemMessage'] = systemMessage[min(i,len(systemMessage))]

            body_dict['prompt'] = user_prompt
            if parent_message_id:
                body_dict['options']['parentMessageId'] = parent_message_id
            # print(body_dict)
            request_message = create_request()

            # 发送请求
            client_socket.sendall(request_message.encode('utf-8'))

            # 接收完整响应
            response = receive_full_response(client_socket)
            header, json_chunk = parse_chunked_response(response)

            # print(json_chunk['text'])
            # responses.append(json_chunk['text'])
            responses = json_chunk['text']
            parent_message_id = json_chunk['id']  # 更新 parent_message_id

        # print("response:"+responses)
        if is_valid_json(responses):
            return responses
        else:
            return {}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

    finally:
        # 关闭socket
        client_socket.close()

if __name__ == "__main__":
    prompts = ["你刚才选的数字是多少", "你刚才选的数字是多少", "你刚才选的数字是多少"]
    responses = query_gpt_api(prompts)
    for response in responses:
        print(response)
