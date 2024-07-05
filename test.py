import json

def format_answer(answer, html_list):
    format_phrase = []
    for phrase in answer["a"]:
        format_phrase.append(phrase)
        for origin_text in html_list:
            if phrase + '<' in origin_text:
                format_phrase[-1] += '<'
                break
    answer["a"] = format_phrase
    return json.dumps(answer, ensure_ascii=False)


if __name__ == "__main__":
    a = ['你好<', '我不好']
    b = {'a': ['你好', '不好']}
    print(format_answer(b, a))