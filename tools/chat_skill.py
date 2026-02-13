class ChatSkill:
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "chat",
                "description": "通用聊天工具。用于处理开放性问题、创意生成、建议提供、常识问答等不需要特定功能的任务。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "用户的问题或请求内容。"
                        },
                        "context": {
                            "type": "string",
                            "description": "对话上下文，用于提供额外的背景信息。"
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict):
        """
        运行通用聊天工具。
        注意：此工具的实际执行逻辑在 app.py 中处理，这里只是提供工具定义。
        """
        query = arguments.get("query", "")
        context = arguments.get("context", "")
        
        # 由于实际的聊天逻辑在 app.py 中处理，这里只返回一个占位符
        # 实际的聊天回复会由 app.py 中的 LLM 调用生成
        return {
            "status": "success",
            "message": "聊天工具已调用",
            "query": query,
            "context": context
        }
