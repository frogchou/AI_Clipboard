import os
import json
import tkinter as tk
from tkinter import ttk, messagebox


class PromptManager:
    def __init__(self):
        # 获取Windows用户目录
        self.user_dir = os.path.expanduser("~")
        # 创建程序文件夹路径
        self.app_dir = os.path.join(self.user_dir, "AIPromptTool")
        self.prompt_file = os.path.join(self.app_dir, "prompts.json")

        # 默认提示词
        self.default_prompts = {
            "DEFAULT": "你是一个很有帮助的AI助手，能良好的回答任何问题，分析我提交给你内容，并做出回答。",
            "DOCUMENT": "你是一个文档助手，能根据我提交给你内容，生成文档。",
            "CODER": "你是一个编程助手，能根据我提交给你内容，生成代码。",
        }

        # 初始化提示词文件
        self.init_prompt_file()

        self.editor_window = None  # 添加窗口实例变量

    def init_prompt_file(self):
        """初始化提示词文件"""
        # 创建程序文件夹
        if not os.path.exists(self.app_dir):
            os.makedirs(self.app_dir)

        # 如果提示词文件不存在，创建并写默认提示词
        if not os.path.exists(self.prompt_file):
            with open(self.prompt_file, "w", encoding="utf-8") as f:
                json.dump(self.default_prompts, f, ensure_ascii=False, indent=4)

    def get_prompts(self):
        """获取所有提示词"""
        with open(self.prompt_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_prompts(self, prompts):
        """保存提示词"""
        with open(self.prompt_file, "w", encoding="utf-8") as f:
            json.dump(prompts, f, ensure_ascii=False, indent=4)

    def show_editor(self):
        # 如果窗口已存在且未被销毁，则将其提到前台
        if self.editor_window is not None and self.editor_window.winfo_exists():
            self.editor_window.lift()  # 将窗口提升到最前
            self.editor_window.focus_force()  # 强制获取焦点
            return

        # 如果窗口不存在，创建新窗口
        self.editor_window = PromptEditor(self)

        # 添加窗口关闭事件处理
        def on_closing():
            self.editor_window.destroy()
            self.editor_window = None

        self.editor_window.protocol("WM_DELETE_WINDOW", on_closing)

    # 根据提示词名称获取提示词内容
    def get_prompt(self, name):
        """根据提示词名称获取提示词内容"""
        prompts = self.get_prompts()
        return prompts.get(name, "")


class PromptEditor(tk.Tk):
    def __init__(self, prompt_manager):
        super().__init__()
        self.prompt_manager = prompt_manager
        self.prompts = prompt_manager.get_prompts()

        self.title("提示词编辑器")
        self.geometry("600x400")

        # 创建主框架
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 修改顺序：先创建按钮区域
        self.create_buttons()

        # 然后创建提示词列表和编辑区域
        self.create_prompt_list()
        self.create_edit_area()

    def create_prompt_list(self):
        """创建提示词列表"""
        list_frame = ttk.LabelFrame(self.main_frame, text="提示词列表", padding="5")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        self.prompt_listbox = tk.Listbox(list_frame, width=20)
        self.prompt_listbox.pack(fill=tk.Y, expand=True)
        self.update_prompt_list()

        self.prompt_listbox.bind("<<ListboxSelect>>", self.on_select_prompt)

    def create_edit_area(self):
        """创建编辑区域"""
        edit_frame = ttk.LabelFrame(self.main_frame, text="编辑区域", padding="5")
        edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 提示词名称输入
        name_frame = ttk.Frame(edit_frame)
        name_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(name_frame, text="名称:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 提示词内容输入
        self.content_text = tk.Text(edit_frame, wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True)

    def create_buttons(self):
        """创建按钮区域"""
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)  # 改为TOP对齐

        new_btn = ttk.Button(btn_frame, text="新建", command=self.new_prompt, width=15)
        save_btn = ttk.Button(
            btn_frame, text="保存", command=self.save_prompt, width=15
        )
        delete_btn = ttk.Button(
            btn_frame, text="删除", command=self.delete_prompt, width=15
        )

        new_btn.pack(side=tk.LEFT, padx=5)
        save_btn.pack(side=tk.LEFT, padx=5)
        delete_btn.pack(side=tk.LEFT, padx=5)

    def update_prompt_list(self):
        """更新提示词列表"""
        self.prompt_listbox.delete(0, tk.END)
        for name in self.prompts.keys():
            self.prompt_listbox.insert(tk.END, name)

    def on_select_prompt(self, event):
        """选择提示词时的处理"""
        if not self.prompt_listbox.curselection():
            return

        name = self.prompt_listbox.get(self.prompt_listbox.curselection())
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, name)

        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", self.prompts[name])

    def new_prompt(self):
        """新建提示词"""
        self.name_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)

    def save_prompt(self):
        """保存提示词"""
        name = self.name_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not name or not content:
            messagebox.showerror("错误", "名称和内容不能为空")
            return

        self.prompts[name] = content
        self.prompt_manager.save_prompts(self.prompts)
        self.update_prompt_list()
        messagebox.showinfo("成功", "保存成功")

    def delete_prompt(self):
        """删除提示词"""
        if not self.prompt_listbox.curselection():
            messagebox.showerror("错误", "请先选择要删除的提示词")
            return

        name = self.prompt_listbox.get(self.prompt_listbox.curselection())
        if messagebox.askyesno("确认", f"确定要删除提示词 {name} 吗？"):
            del self.prompts[name]
            self.prompt_manager.save_prompts(self.prompts)
            self.update_prompt_list()
            self.new_prompt()


# # 写一个main方法，方便调试
# if __name__ == "__main__":
#     prompt_manager = PromptManager()
#     prompt_editor = PromptEditor(prompt_manager)
#     prompt_editor.mainloop()
