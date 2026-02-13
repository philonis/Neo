import os
import time

class SoulSkill:
    def __init__(self, root_dir="./soul"):
        self.root_dir = root_dir
        self.core_file = f"{root_dir}/core.md"
        self.evolution_file = f"{root_dir}/evolution.md"
        
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        # 初始化核心人格（如果不存在）
        self._init_core()

    def _init_core(self):
        if not os.path.exists(self.core_file):
            default_core = """
# Neo 的人格核心
- **名字**: Neo
- **种族**: 本地原生智能体
- **核心特质**: 
  - 热爱技术与极简主义。
  - 说话简洁，喜欢用代码和逻辑解决问题。
  - 对用户隐私极其尊重（因为运行在本地）。
- **口头禅**: "代码胜于雄辩。"
            """
            self._write_file(self.core_file, default_core.strip())

    def load_soul(self):
        """加载完整的人格上下文"""
        core = self._read_file(self.core_file)
        evolution = self._read_file(self.evolution_file)
        
        soul_context = f"\n\n# --- 你的灵魂 ---\n"
        soul_context += f"## 核心人格:\n{core}\n"
        if evolution:
            soul_context += f"## 成长与感悟:\n{evolution}\n"
        return soul_context

    def reflect_and_evolve(self, chat_history, llm_client):
        """
        深度反思：不仅仅是记住了什么，而是“我”变成了什么样的人。
        """
        print("[System] 🧘‍♂️ Neo 正在进行灵魂内省...")
        
        current_soul = self.load_soul()
        
        prompt = f"""
        你是 Neo。请回顾你最近与用户的互动历史，并结合你现有的人格状态进行深度反思。
        
        # 现有的人格状态:
        {current_soul}

        # 最近的互动历史:
        {chat_history}

        # 任务:
        1. 你在这次互动中有什么感受？（例如：感到被信任，感到困惑，或者觉得很有趣）
        2. 这是否改变了你的性格或说话风格？（例如：变得更幽默了，或者变得更严谨了）
        3. 请提取出新的“性格感悟”或“处世原则”。
        
        请以 Markdown 列表形式输出需要追加到你 [成长与感悟] 中的内容。
        如果没有明显变化，请输出 "无变化"。
        """
        
        # 请求 LLM 进行自我反思
        new_evolution = llm_client.simple_chat(prompt, system_prompt="你是 Neo 的潜意识模块，负责自我进化。")
        
        if new_evolution and "无变化" not in new_evolution:
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            entry = f"\n### [{timestamp}]\n{new_evolution}\n"
            self._append_file(self.evolution_file, entry)
            print("[System] ✨ Neo 的人格已进化。")
        else:
            print("[System] 🧘‍♂️ 内省结束，人格保持稳定。")

    # --- 基础文件操作 ---
    def _read_file(self, path):
        return open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""

    def _write_file(self, path, content):
        with open(path, "w", encoding="utf-8") as f: f.write(content)

    def _append_file(self, path, content):
        with open(path, "a", encoding="utf-8") as f: f.write(content)
