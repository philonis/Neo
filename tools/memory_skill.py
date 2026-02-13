import os
import time

class PersonalMemorySkill:
    def __init__(self, root_dir="./memory"):
        self.root_dir = root_dir
        self.active_file = f"{root_dir}/current_chat.md"
        self.traits_file = f"{root_dir}/persona_traits.md"
        
        # 阈值设定：超过 2000 字符触发压缩（根据你的模型窗口调整）
        self.CONSOLIDATION_THRESHOLD = 2000 
        
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)

    def load_context(self):
        """
        在 CLI 启动时调用：加载合并后的记忆供 System Prompt 使用
        """
        traits = self._read_file(self.traits_file)
        recent_chat = self._read_file(self.active_file)
        
        # 只有在文件有内容时才添加描述
        context_block = ""
        if traits or recent_chat:
            context_block += "\n\n# --- 本地记忆系统 (注入) ---\n"
            if traits:
                context_block += f"## 用户画像与长期记忆:\n{traits}\n"
            if recent_chat:
                context_block += f"## 近期对话摘要:\n{recent_chat}\n"
            context_block += "--------------------------------\n"
            
        return context_block

    def record_interaction(self, user_input, ai_response, llm_client):
        """
        每轮对话结束时调用：记录并判断是否需要触发“记忆蒸馏”
        """
        # 1. 写入明文活跃记忆
        entry = f"User: {user_input}\nAI: {ai_response}\n\n"
        self._append_file(self.active_file, entry)
        
        # 2. 检查是否超出阈值
        if os.path.exists(self.active_file) and os.path.getsize(self.active_file) > self.CONSOLIDATION_THRESHOLD:
            print("\n[System] 🧠 记忆缓存已满，正在后台压缩提炼长期记忆...")
            self.consolidate(llm_client)

    def consolidate(self, llm_client):
        """
        记忆固化核心逻辑：将“经历”转化为“认知”
        """
        raw_memory = self._read_file(self.active_file)
        existing_traits = self._read_file(self.traits_file)
        
        distill_prompt = f"""
        你是一个记忆管理器。请分析以下【近期对话片段】，提取关键信息更新【现有用户画像】。

        ## 现有用户画像:
        {existing_traits if existing_traits else "暂无"}

        ## 近期对话片段:
        {raw_memory}

        ## 任务要求:
        1. 提取核心事实（如：用户从事IT行业，用户养了一只猫）。
        2. 提取用户偏好（如：喜欢简洁的回答，不喜欢代码解释）。
        3. 去除冗余信息，只保留有助于未来交互的关键特征。
        
        请直接输出更新后的 Markdown 格式的用户画像（不要包含 "```" 包裹符）：
        """

        # 获取 LLM 蒸馏后的结论 (使用 simple_chat)
        new_traits = llm_client.simple_chat(distill_prompt, system_prompt="你是专业的记忆管理助手。")
        
        if new_traits:
            # 3. 更新认知文件
            self._write_file(self.traits_file, new_traits)
            print("[System] ✅ 长期记忆已更新。")
            
            # 4. 归档原始记录并清空活跃区
            self._archive_raw_data(raw_memory)
            self._clear_file(self.active_file)

    def _archive_raw_data(self, content):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        # 归档文件名加上时间戳，方便查阅
        archive_path = f"{self.root_dir}/archive_{timestamp}.md"
        self._write_file(archive_path, content)

    # --- 基础文件操作 ---
    def _read_file(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _append_file(self, path, content):
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)

    def _write_file(self, path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _clear_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.truncate() # 清空文件内容
