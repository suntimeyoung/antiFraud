import socket
import json

# GPT参数配置信息
body_dict = {}
server_ip = '192.168.75.198'
server_port = 3002

# 修改gpt设置参数
body_dict['options'] = {}
body_dict['temperature'] = 0.9
body_dict['top_p'] = 0.8
systemMessage_filepath = 'systemMessage/systemMessage.txt'

def read_file_to_string(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content


def create_request():
    body = json.dumps(body_dict, ensure_ascii=False)
    content_length = len(body.encode('utf-8'))

    request_line = "POST /api/chat-process HTTP/1.1\r\n"
    headers = (
        f"Host: 192.168.75.198:3002\r\n"
        "Connection: close\r\n"
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
        if not part or part[-5:] == b'0\r\n\r\n':
            break
        response += part
    return response

def parse_chunked_response(response):
    header, body = response.split(b"\r\n\r\n", 1)
    json_chuck = {}
    while body:
        chunk_size_str, body = body.split(b"\r\n", 1)
        chunk_size = int(chunk_size_str, 16)
        if chunk_size == 0:
            break
        chunk, body = body[:chunk_size], body[chunk_size+2:]  # +2 to remove \r\n after chunk
        json_chuck = json.loads(chunk.decode('utf-8'))
    return header.decode('utf-8'), json_chuck

def query_gpt_api(user_prompt):
    body_dict['prompt'] = user_prompt
    body_dict['systemMessage'] = read_file_to_string(systemMessage_filepath)

    request_message = create_request()

    # 创建socket对象
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接服务器
        client_socket.connect((server_ip, server_port))

        # 发送请求
        client_socket.sendall(request_message.encode('utf-8'))

        # 接收完整响应
        response = receive_full_response(client_socket)
        header, json_chuck = parse_chunked_response(response)

        return json_chuck['text']

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # 关闭socket
        client_socket.close()

if __name__ == "__main__":
    json_chuck = query_gpt_api("你好")
    print(json_chuck)