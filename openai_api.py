import os
import time
from openai import OpenAI
from dotenv import load_dotenv


def read_file_to_string(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content


class GPT:
    def __init__(self):
        self.temperature = 0.3
        self.top_p = 0.9
        self.total_tokens = 0
        self.total_rounds = 0
        self.max_tokens = 200
        self.total_time = time.time()
        self.last_time = 0
        self.min_interval = 1
        self.prompt_dir = './prompt/'

        # 获取 API 密钥
        load_dotenv()
        self.client = OpenAI(
            api_key = os.environ.get("OPENAI_API_KEY"),
            base_url = os.environ.get("OPENAI_BASE_URL"),
        )

    def query_api_bare(self, message: list[dict]):
        # 控制api访问速率
        interval = time.time() - self.last_time
        if interval < self.min_interval:
            time.sleep(self.min_interval - interval)
        self.last_time = time.time()

        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            # response_format={"type": "json_object"},
            messages=message,
            max_tokens=self.max_tokens
        )
        # 提取回答
        answer = completion.choices[0].message.content
        self.total_rounds += 1
        self.total_tokens += completion.usage.total_tokens
        print(f"||| total_tokens = {completion.usage.total_tokens}")
        return answer

    def query_api_sectional(self, html_str):
        response = html_str
        for i in range(1, 3):
            prompt = read_file_to_string(f"{self.prompt_dir}prompt_{i}.txt")
            response = self.query_api_bare([
                {"role": "system", "content": "You are an experienced and helpful web fraud examiner"},
                {"role": "user", "content": prompt + '\n' + response}
            ])
            # print(response)
        return response

    def query_api_single(self, html_str):
        prompt = read_file_to_string(f"{self.prompt_dir}prompt.txt")
        response = self.query_api_bare([
            {"role": "system", "content": prompt},
            {"role": "user", "content": html_str}
        ])
        return response

if __name__ == "__main__":
    gpt = GPT()
    message = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
    ]
    answer = gpt.query_api_bare(message)
    print(answer)


