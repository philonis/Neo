import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import LLMClient

class ChatSkill:
    _client = None
    
    @classmethod
    def _get_client(cls):
        if cls._client is None:
            cls._client = LLMClient()
        return cls._client
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "chat",
                "description": "通用聊天工具。用于处理开放性问题、创意生成、建议提供、常识问答、旅行建议、生活建议等不需要特定功能的任务。当用户只是想聊天或问一般性问题时使用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "对用户问题的回复内容。"
                        }
                    },
                    "required": ["response"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict):
        response = arguments.get("response", "")
        
        if not response:
            return {
                "status": "error",
                "message": "回复内容不能为空"
            }
        
        return {
            "status": "success",
            "message": "回复已生成",
            "response": response
        }
