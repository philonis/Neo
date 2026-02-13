from llm_client import LLMClient
# 引入上一节定义的工具类和定义
from tools.notes_skill import NotesSkill 

def run_agent(user_prompt):
    # 1. 初始化客户端
    client = LLMClient() # 确保你设置了正确的 API Key

    # 2. 准备初始消息
    messages = [
        {"role": "system", "content": "你是一个本地助手，可以使用 macOS 备忘录工具帮用户记录事情。"},
        {"role": "user", "content": user_prompt}
    ]

    # 3. 获取工具定义
    tools_schema = [NotesSkill.get_tool_definition()]

    print(f"\n>>> 用户输入: {user_prompt}")
    print(">>> 正在思考...")

    # 4. 第一次调用 LLM (询问是否需要调用工具)
    response_data = client.chat(messages, tools=tools_schema)

    if not response_data:
        print("LLM 调用失败")
        return

    message = response_data["choices"][0]["message"]

    # 5. 检查是否需要调用工具
    if message.get("tool_calls"):
        # 通常只会有一个 tool_call，这里取第一个
        tool_call = message["tool_calls"][0]
        func_name = tool_call["function"]["name"]
        func_args_str = tool_call["function"]["arguments"]
        
        print(f">>> 决定调用工具: {func_name}")
        print(f">>> 参数: {func_args_str}")

        # 6. 执行本地工具
        if func_name == "notes_operator":
            args = json.loads(func_args_str)
            tool_result = NotesSkill.run(args)
            
            print(f">>> 工具执行结果: {tool_result}")

            # 7. 将工具执行结果回传给 LLM，让它生成最终回复
            # 构建历史消息：原始请求 + 工具调用请求 + 工具返回结果
            messages.append(message) # 把 LLM 想要调工具的请求加入历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": func_name,
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

            # 8. 第二次调用 LLM (生成最终给用户的自然语言回复)
            final_response = client.chat(messages)
            final_content = final_response["choices"][0]["message"]["content"]
            print(f"\n>>> 最终回复: {final_content}")
        else:
            print(">>> 未知工具调用")
            
    else:
        # 没有工具调用，直接回复
        print(f"\n>>> 直接回复: {message['content']}")

if __name__ == "__main__":
    import json
    
    # 测试场景：用户的话包含了“记一下”，应该触发备忘录工具
    run_agent("帮我在备忘录里记一下，明天下午3点要开会。")
