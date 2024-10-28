class AIChatHistory:
    def __init__(self):
        """
        初始化聊天历史记录类
        chat_history: 用于存储聊天记录的列表
        每条记录的格式为 {"role": "user/assistant", "content": [...]}
        """
        self.chat_history = []

    def add_message(self, role: str, content: str, content_type: str = "text"):
        """
        添加一条聊天记录
        :param role: 发言角色 ("user" 或 "assistant")
        :param content: 发言内容
        :param content_type: 内容类型 (默认为 "text")
        """
        if role not in ["user", "assistant", "system"]:
            raise ValueError("角色必须是 'user', 'assistant' 或 'system'")

        message = {"role": role, "content": [{"type": content_type, "text": content}]}

        self.chat_history.append(message)

    def clear_history(self):
        """
        清空所有聊天记录
        """
        self.chat_history = []

    def get_history(self):
        """
        获取所有聊天记录
        :return: 聊天记录列表
        """
        return self.chat_history

    def get_formatted_history(self):
        """
        获取格式化后的聊天记录，直接可用于API调用
        :return: 格式化的聊天记录列表
        """
        return self.chat_history

    def get_last_n_messages(self, n: int):
        """
        获取最后n条聊天记录
        :param n: 需要获取的记录数量
        :return: 最后n条聊天记录
        """
        return self.chat_history[-n:] if n > 0 else []

    def add_system_message(self, content: str):
        """
        添加系统消息
        :param content: 系统消息内容
        """
        self.add_message("system", content)

    def message_count(self):
        """
        获取当前聊天记录的数量
        :return: 记录数量
        """
        return len(self.chat_history)
