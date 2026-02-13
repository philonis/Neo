import requests
import json
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv() 

class LLMClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        # 优先级：传入参数 > .env环境变量 > 默认值
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.qnaigc.com/v1/chat/completions")
        self.model = model or os.getenv("LLM_MODEL", "deepseek/deepseek-v3.2-251201")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(self, messages, tools=None, stream=False):
        """
        发送对话请求
        
        :param messages: 对话历史列表 [{"role": "user", "content": "..."}]
        :param tools: 工具定义列表 (可选)
        :param stream: 是否流式输出 (暂未完全实现处理逻辑)
        :return: 解析后的 JSON 响应
        """
        payload = {
            "stream": stream,
            "model": self.model,
            "messages": messages
        }

        # 如果有传入工具定义，加入 payload
        if tools:
            payload["tools"] = tools

        try:
            response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=60)
            response.raise_for_status() # 检查 HTTP 错误
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[LLM Client Error] 请求失败: {e}")
            return None
        except json.JSONDecodeError:
            print(f"[LLM Client Error] 响应解析失败: {response.text}")
            return None

    def simple_chat(self, user_content, system_prompt="You are a helpful assistant."):
        """
        简单对话封装，适合不需要工具的快速调用
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        result = self.chat(messages)
        
        if result and "choices" in result:
            return result["choices"][0]["message"]["content"]
        return None

# --- 模块测试代码 ---
if __name__ == "__main__":
    # 测试：直接运行此文件
    client = LLMClient()
    
    print("正在进行简单对话测试...")
    reply = client.simple_chat("你好，请用一句话介绍你自己。")
    print(f"模型回复: {reply}")
