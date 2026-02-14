import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.qnaigc.com/v1/chat/completions")
        self.model = model or os.getenv("LLM_MODEL", "deepseek/deepseek-v3.2-251201")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }

    def chat(self, messages, tools=None, tool_choice="auto", stream=False):
        """
        发送对话请求，支持原生 Function Calling
        
        :param messages: 对话历史列表
        :param tools: 工具定义列表 (OpenAI 格式)
        :param tool_choice: "auto" | "none" | {"type": "function", "function": {"name": "..."}}
        :param stream: 是否流式输出
        :return: 解析后的响应
        """
        payload = {
            "stream": stream,
            "model": self.model,
            "messages": messages
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        try:
            response = requests.post(
                self.base_url, 
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), 
                headers=self.headers, 
                timeout=120
            )
            response.encoding = 'utf-8'
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[LLM Client Error] 请求失败: {e}")
            return None
        except json.JSONDecodeError:
            print(f"[LLM Client Error] 响应解析失败")
            return None

    def chat_with_tools(self, messages, tools, max_tool_calls=10):
        """
        高级封装：自动处理工具调用循环
        
        :param messages: 对话历史
        :param tools: 可用工具列表
        :param max_tool_calls: 最大工具调用次数
        :return: (final_response, tool_call_history)
        """
        tool_call_history = []
        
        for _ in range(max_tool_calls):
            response = self.chat(messages, tools=tools, tool_choice="auto")
            
            if not response:
                return None, tool_call_history
            
            message = response["choices"][0]["message"]
            
            if "tool_calls" in message and message["tool_calls"]:
                messages.append(message)
                
                for tool_call in message["tool_calls"]:
                    args_str = tool_call["function"]["arguments"]
                    if isinstance(args_str, str):
                        args = json.loads(args_str)
                    else:
                        args = args_str if isinstance(args_str, dict) else {}
                    tool_call_history.append({
                        "id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "arguments": args
                    })
                
                return response, tool_call_history
            
            messages.append(message)
            return response, tool_call_history
        
        return None, tool_call_history

    def simple_chat(self, user_content, system_prompt="You are a helpful assistant."):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        result = self.chat(messages)
        
        if result and "choices" in result:
            return result["choices"][0]["message"]["content"]
        return None

    def extract_response_content(self, response):
        if not response or "choices" not in response:
            return None
        message = response["choices"][0]["message"]
        return message.get("content")

    def extract_tool_calls(self, response):
        if not response or "choices" not in response:
            return []
        message = response["choices"][0]["message"]
        return message.get("tool_calls", [])

    def has_tool_calls(self, response):
        if not response:
            return False
        tool_calls = self.extract_tool_calls(response)
        return len(tool_calls) > 0
