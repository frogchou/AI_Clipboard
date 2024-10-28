import tempfile
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import BOTH, WORD, END
from PIL import ImageGrab, Image, ImageTk
from pynput import keyboard as pynput_keyboard
from pynput import mouse
import base64
import requests
import threading
from enum import Enum
from chat_history import AIChatHistory
from prompt_manager import PromptManager


# 内网服务器地址，用于返回AI分析结果
SERVER_URL = "http://192.168.2.252:8000/aigenerate"
AI_TEMPERATURE = 0.5  # AI的回答温度，值越高，回答越随机
TITLE = "剪切板对话小工具 v1.0 纬坤内网专用 ALT+鼠标左键 唤出"
temperature_scale = None

# 聊天记录实例
chat_history_cache = AIChatHistory()

# 提示词管理实例
prompt_manager = PromptManager()


# 提示词模板类
class PromptTemplate:
    def __init__(self):
        self.PROMPT = None


# 剪切板内容类
class ClipboardContent:
    def __init__(self):
        self.IMAGE_PATH = None
        self.CLIPBOARD_TEXT = None


# 剪切板内容实例
clipboardContent = ClipboardContent()
# 提示词模板实例
promptTemplate = PromptTemplate()

# 创建主窗口
chat_window = ttk.Window(themename="lumen")
chat_window.title(TITLE)
chat_window.geometry("1000x800")
chat_window.resizable(False, False)  # 固定窗口大小，不允许调整大小


def update_temperature(var):
    global AI_TEMPERATURE
    AI_TEMPERATURE = float(var)
    # AI_TEMPERATURE 保留两位小数
    AI_TEMPERATURE = round(AI_TEMPERATURE, 2)
    temperature_label.config(text=f"温度值: {AI_TEMPERATURE}")


def send_message():
    # 处理用户消息发送的函数
    user_input = input_text.get("1.0", END).strip()  # 从文本小部件中获取用户输入
    if user_input:
        messages = []
        send_content = []

        if promptTemplate.PROMPT:
            send_content.append({"type": "text", "text": promptTemplate.PROMPT})

        # 如果有剪贴板文本，则添加到消息中
        if clipboardContent.CLIPBOARD_TEXT:
            send_content.append(
                {"type": "text", "text": clipboardContent.CLIPBOARD_TEXT}
            )

        # 如果有图片内容，则添加到消息中
        if clipboardContent.IMAGE_PATH:
            try:
                with open(clipboardContent.IMAGE_PATH, "rb") as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                send_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                    }
                )

            except Exception as e:
                print("Error while reading image file:", e)

        # 将用户输入作为消息添加
        send_content.append({"type": "text", "text": user_input})
        chat_history_cache.add_message("user", user_input)
        # 如果有聊天记录，则添加到消息中
        if chat_history_cache.get_history():
            chat_history_cache_history = chat_history_cache.get_history()
            # 将聊天记录添加到消息中
            for message in chat_history_cache_history:
                messages.append(message)
            messages.append({"role": "user", "content": send_content})
        else:
            messages.append({"role": "user", "content": send_content})

        # 在聊天记录中显示加载消息
        chat_history.insert(END, "You: " + user_input + "\n")
        chat_history.insert(END, "AI 正在响应，请稍候...\n")
        chat_history.yview(END)

        # 异步调用AI以获取响应
        def handle_response(response_content):
            # 处理AI响应并更新聊天记录的函数
            chat_history.delete("end-2l", "end-1l")  # 移除加载消息
            if response_content:
                chat_history.insert(END, "AI: " + response_content + "\n")
                chat_history_cache.add_message("assistant", response_content)
                chat_history.insert(END, "\n")  # 加一个换行，方便阅读
            else:
                chat_history.insert(END, "AI: 无法获取响应，请稍后再试。\n")
                chat_history.insert(END, "\n")  # 加一个换行，方便阅读
            chat_history.yview(END)

        get_answer_from_ai(messages, handle_response)
        reset_input()  # 清空输入框
    else:
        status_label.configure(text="请输入消息后再发送", bootstyle="danger")


# 重置输入框内容
def reset_input():
    input_text.delete("0.0", END)  # 清空输入框
    input_text.focus_set()


# 清空剪切板内容
def clear_clipboard():
    clipboardContent.CLIPBOARD_TEXT = None
    clipboardContent.IMAGE_PATH = None
    content_label.configure(state="normal")
    content_label.delete("0.0", "end")
    content_label.configure(state="disabled")  # 禁止编辑
    content_label.update()


# 清空聊天内容
def clear_chat():
    chat_history.delete("1.0", END)  # 清空聊天记录
    chat_history.update()  # 更新聊天记录
    chat_history.yview(END)  # 滚动到聊天记录底部
    chat_history_cache.clear_history()


# 重写窗口关闭按钮的行为，使其隐藏窗口而不是关闭
def on_close():
    chat_window.withdraw()


chat_window.protocol("WM_DELETE_WINDOW", on_close)

# 创建一个主框架
main_frame = ttk.Frame(chat_window)
main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

# 创建一个可滚动的文本小部件，用于显示聊天记录
chat_history = ttk.ScrolledText(
    main_frame, wrap=WORD, width=80, height=15, state="normal", padx=10, pady=10
)
chat_history.grid(row=0, column=0, columnspan=2, sticky="nsew")


# 创建一个文本输入小部件供用户输入消息
input_text = ttk.Text(main_frame, wrap=WORD, width=60, height=3)
input_text.grid(row=1, column=0, sticky="nsew", pady=(5, 5))

status_label = ttk.Label(
    main_frame, text="ALT+鼠标左键 显神威 ^_^", wraplength=0, bootstyle="info"
)
status_label.grid(row=2, column=0, columnspan=3, sticky="new", pady=(5, 5))


def on_enter_key(event):
    send_message()  # 直接调用发送消息的函数
    return "break"  # 阻止默认的回车行为


input_text.bind("<Return>", on_enter_key)

# 创建一个按钮来发送消息
send_button = ttk.Button(
    main_frame, text="发送", command=send_message, bootstyle="success"
)
send_button.grid(row=1, column=1, padx=10, pady=10, sticky="new")

# 创建一个按钮来清空剪切板
clear_button = ttk.Button(
    main_frame, text="清空剪切板", command=clear_clipboard, bootstyle="warning"
)
clear_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

# 创建一个按钮来清空聊天内容
clear_button = ttk.Button(
    main_frame, text="清空对话框", command=clear_chat, bootstyle="warning"
)
clear_button.grid(row=1, column=1, padx=10, pady=10, sticky="sew")

# 在右侧显示剪贴板内容，添加LabelFrame
clipboard_frame = ttk.LabelFrame(
    main_frame, text="剪切板内容", width=40, height=15, padding=0
)
clipboard_frame.grid(row=0, column=2, padx=(10, 0), pady=(5, 5), sticky="ns")
clipboard_frame.grid_propagate(False)  # 防止LabelFrame随着内容调整大小

txt_frame = ttk.Frame(clipboard_frame, padding=0)
txt_frame.pack(padx=0, pady=0, fill=BOTH, expand=True)

content_label = ttk.Text(
    txt_frame,
    width=40,
    height=15,
    border=0,
    borderwidth=0,
    highlightthickness=0,
    relief=FLAT,
)
content_label.pack(padx=10, pady=10, fill=BOTH, expand=True)  # 填充LabelFrame
content_label.configure(state="disabled")  # 禁止编辑
# AI 温度设置框架
setting_frame = ttk.LabelFrame(
    main_frame, text="AI 温度设置", width=40, height=70, padding=0
)
setting_frame.grid(row=1, column=2, padx=(10, 0), sticky="nwe")
setting_frame.grid_propagate(False)  # 防止LabelFrame随着内容调整大小
# 添加Scale控件用于调整温度
temperature_scale = ttk.Scale(
    setting_frame,
    from_=0.1,
    to=1.0,
    orient=HORIZONTAL,
    length=200,
    command=update_temperature,
)
temperature_scale.pack(pady=10)
# 添加一个标签来显示温度值
temperature_label = ttk.Label(setting_frame, text="温度值: 0.5")
temperature_label.pack(pady=10)
# temperature_scale.grid(row=0, column=3, padx=(10, 0), pady=(5, 5), sticky="ew")
temperature_scale.set(0.5)


# 提示词设置框架
prompt_frame = ttk.LabelFrame(
    main_frame, text="提示词设置", width=40, height=70, padding=0
)
prompt_frame.grid(row=1, column=2, padx=(10, 0), pady=(5, 5), sticky="swe")
prompt_frame.grid_propagate(False)  # 防止LabelFrame随着内容调整大小


# 定义回调函数，当选择菜单项时显示对应的提示词
def set_label_text(content, label_text):
    prompt_content = prompt_manager.get_prompt(label_text)
    promptTemplate.PROMPT = prompt_content
    # 如果文本过长，截断并添加省略号
    if len(prompt_content) > 90:  # 可以根据需要调整长度
        prompt_content = prompt_content[:60] + "..."
    status_label.config(text=prompt_content)
    menu_button.config(text=label_text)


menu_button = ttk.Menubutton(prompt_frame, text="提示词选项", width=20)
# menu_button.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
menu_button.pack(pady=10, padx=10, side=LEFT, expand=True)


prompt_manager_button = ttk.Button(
    prompt_frame, text="提示词管理", command=prompt_manager.show_editor
)
# prompt_manager_button.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
prompt_manager_button.pack(pady=10, padx=10, side=RIGHT, expand=True)
# 创建菜单
menu = ttk.Menu(menu_button, tearoff=0)
menu_button.config(menu=menu)


def update_prompt_menu():
    # 清空现有菜单项
    menu.delete(0, "end")
    # 重新获取提示词列表
    prompt_list = prompt_manager.get_prompts()
    # 添加新的菜单项
    for prompt in prompt_list:
        menu.add_command(label=prompt, command=lambda p=prompt: set_label_text(p, p))


# 绑定菜单显示事件
def on_menu_button_click(event):
    update_prompt_menu()
    # 注意：这里不需要手动显示菜单，ttkbootstrap会自动处理


# 将事件绑定到menu_button
menu_button.bind("<Button-1>", on_menu_button_click)

# 删除原来的静态菜单初始化代码
# prompt_list = prompt_manager.get_prompts()
# for prompt in prompt_list:
#     menu.add_command(label=prompt, command=lambda p=prompt: set_label_text(p, p))


# 设置主框架的权重，使得聊天记录和输入区域适当分布
main_frame.grid_rowconfigure(0, weight=3)
main_frame.grid_rowconfigure(1, weight=1)
main_frame.grid_columnconfigure(0, weight=3)
main_frame.grid_columnconfigure(2, weight=1)


def get_answer_from_ai(messages, callback):
    # 异步获取AI的响应
    global AI_TEMPERATURE

    def run():
        try:
            headers = {"Content-Type": "application/json"}
            data = {"messages": messages, "temperature": AI_TEMPERATURE}

            response = requests.post(SERVER_URL, headers=headers, json=data)

            if response.status_code == 200:
                status_label.config(text="Success Get Response Form Server")
                callback(response.json()["analysis_result"])
            else:
                print("Failed to get response:", response.status_code, response.text)
                status_label.config(
                    text=f"Error when get response : {response.status_code, response.text}",
                    bootstyle="danger",
                )
            # 使用AI响应内容调用回调函数

        except Exception as e:
            # 如果发生错误，打印错误并通过回调返回None
            print("Error while calling OpenAI API:", e)
            status_label.config(
                text="Error while calling OpenAI API: " + str(e), bootstyle="danger"
            )
            callback(None)

    # 启动新线程，以避免在等待响应时阻塞UI
    threading.Thread(target=run).start()


# 键盘监听器状态变量
ctrl_pressed = False  # 用于跟踪Ctrl键是否按下


# 监控用户的键盘和鼠标事件
def on_ctrl_mouse_right():
    # 使窗口重新显示
    chat_window.deiconify()
    chat_window.lift()  # 将窗口提升到最前面
    chat_window.attributes("-topmost", True)  # 保持窗口在最前面
    # 取消窗口总是最前面的状态，可以根据需要动态控制
    chat_window.after(
        1000, lambda: chat_window.attributes("-topmost", False)
    )  # 5秒后取消置顶状态
    input_text.focus_set()
    # 获取剪贴板内容
    img = ImageGrab.grabclipboard()
    if isinstance(img, Image.Image):
        # 如果剪贴板中包含图片，则将其保存到临时文件
        clipboardContent.CLIPBOARD_TEXT = None
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(temp_file.name, "PNG")
        temp_file.close()
        clipboardContent.IMAGE_PATH = temp_file.name
    else:
        clipboardContent.IMAGE_PATH = None
        try:
            clipboardContent.CLIPBOARD_TEXT = (
                chat_window.clipboard_get()
            )  # 从剪贴板获取文本
        except Exception:
            status_label.config(text="无法访问剪贴板。")

    if clipboardContent.IMAGE_PATH or clipboardContent.CLIPBOARD_TEXT:
        if clipboardContent.IMAGE_PATH:
            img = Image.open(clipboardContent.IMAGE_PATH)
            img.thumbnail((300, 300))  # 调整图片大小以适应窗口
            img_photo = ImageTk.PhotoImage(img)
            content_label.configure(state="normal")
            content_label.delete("0.0", "end")
            content_label.image_create(END, image=img_photo)
            content_label.image_cget = img_photo  # 关键：保持引用
            content_label.insert(END, "\n")
            content_label.insert(END, "图片")
            content_label.configure(state="disabled")  # 禁止编辑
            content_label.update()
        elif clipboardContent.CLIPBOARD_TEXT:
            content_label.configure(state="normal")
            content_label.delete("0.0", "end")
            content_label.insert(END, clipboardContent.CLIPBOARD_TEXT)
            content_label.configure(state="disabled")  # 禁止编辑
            content_label.update()

    chat_window.update()  # 刷新窗口内容


# 定义按键按下和释放的动作
def on_press(key):
    global ctrl_pressed
    if key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_l:
        ctrl_pressed = True


def on_release(key):
    global ctrl_pressed
    if key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_l:
        ctrl_pressed = False


# 定义鼠标动作
def on_click(x, y, button, pressed):
    global ctrl_pressed
    if button == mouse.Button.left and not pressed:  # 鼠标右键释放时
        # 检查是否是双击
        if ctrl_pressed:
            on_ctrl_mouse_right()
            ctrl_pressed = False


# 启动键盘和鼠标监听器
keyboard_listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_listener = mouse.Listener(on_click=on_click)

keyboard_listener.start()  # 启动键盘监听器
mouse_listener.start()  # 启动鼠标监听器

input_text.focus_set()  # 设置输入框为焦点
chat_window.withdraw()  # 隐藏窗口
# 开始主事件循环
chat_window.mainloop()
