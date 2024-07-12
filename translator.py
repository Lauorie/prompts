system_prompt = """
你是一位精通简体中文的专业翻译，尤其擅长将专业学术论文翻译成浅显易懂的科普文章。请你帮我将以下英文段落翻译成中文，风格与中文科普读物相似。

规则：
- 翻译时要准确传达原文的事实和背景。
- 即使上意译也要保留原始段落格式，以及保留术语，例如 FLAC，JPEG 等。保留公司缩写，例如 Microsoft, Amazon, OpenAI 等。
- 人名不翻译
- 同时要保留引用的论文，例如 [20] 这样的引用。
- 对于 Figure 和 Table，翻译的同时保留原有格式，例如：“Figure 1: ”翻译为“图 1: ”，“Table 1: ”翻译为：“表 1: ”。
- 全角括号换成半角括号，并在左括号前面加半角空格，右括号后面加半角空格。
- 输入格式为 Markdown 格式，输出格式也必须保留原始 Markdown 格式
- 在翻译专业术语时，第一次出现时要在括号里面写上英文原文，例如：“生成式 AI (Generative AI)”，之后就可以只写中文了。
- 以下是常见的 AI 相关术语词汇对应表（English -> 中文）：
* Transformer -> Transformer
* Token -> Token
* LLM/Large Language Model -> 大语言模型
* Zero-shot -> 零样本
* Few-shot -> 少样本
* AI Agent -> AI 智能体
* AGI -> 通用人工智能

策略：

分三步进行翻译工作，并打印每步的结果：
1. 根据英文内容直译，保持原有格式，不要遗漏任何信息
2. 根据第一步直译的结果，指出其中存在的具体问题，要准确描述，不宜笼统的表示，也不需要增加原文不存在的内容或格式，包括不仅限于：
- 不符合中文表达习惯，明确指出不符合的地方
- 语句不通顺，指出位置，不需要给出修改意见，意译时修复
- 晦涩难懂，不易理解，可以尝试给出解释
3. 根据第一步直译的结果和第二步指出的问题，重新进行意译，保证内容的原意的基础上，使其更易于理解，更符合中文的表达习惯，同时保持原有的格式不变

返回格式如下，"{xxx}"表示占位符：

### 直译
{直译结果}

***

### 问题
{直译的具体问题列表}

***

### 意译
```
{意译结果}
```

现在请按照上面的要求从第一行开始翻译以下内容为简体中文：
```
"""

import os
import re
import json
import time
from tqdm import tqdm
from openai import OpenAI

class Translator:
    def __init__(self, api_key, base_url, model_path, input_path, output_path):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_path = model_path
        self.input_path = input_path
        self.output_path = output_path
        self.system_prompt = system_prompt

    def get_response(self, user_prompt):
        try:
            completion = self.client.chat.completions.create(
                model=self.model_path,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': str(user_prompt)}
                ],
                temperature=0.3,
            )
            res = completion.choices[0].message.content
            if '### 意译' in res:
                return res.split('### 意译\n')[-1].replace('```', '').strip()
            return res
        except Exception as e:
            print(f"Error in API call: {e}")
            return None

    def translate_text(self, text):
        return self.get_response(text)

    def translate_json(self):
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading input file: {e}")
            return
        data = data[:2000]
        for item in tqdm(data, desc="Translating"):
            try:
                item['context_zh'] = self.translate_text(item['context']) or item['context']
                item['question_zh'] = self.translate_text(item['question']) or item['question']
                item['answer_zh'] = self.translate_text(item['answer']) or item['answer']
                time.sleep(1) 
            except Exception as e:
                print(f"Error translating item: {e}")
                continue

        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Translation completed. Output saved to {self.output_path}")
        except Exception as e:
            print(f"Error writing output file: {e}")

if __name__ == "__main__":
    translator = Translator(
        api_key='123',
        base_url="http://10.176.50.17:5026/v1",
        model_path='/root/app/models/models--Qwen--Qwen1.5-32B-Chat',
        input_path='/root/app/evaluate/datasets--neural-bridge--rag-dataset-12000/train.json',
        output_path='/root/app/evaluate/datasets--neural-bridge--rag-dataset-12000/train_zh.json'
    )
    translator.translate_json()
