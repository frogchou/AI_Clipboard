#########################################################################################
# 特别说明：
# 以下是内网服务器的代码，供参考。
#########################################################################################

from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from datetime import datetime
import uvicorn
from openai import OpenAI
import base64
import os

app = FastAPI()

# 环境变量中存储的 OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = (
    "http://XXX.frogchou.com/XXXX"  # 国内需要使用一个反向代理服务器，国外不需要
)

AI_TEMPERATURE = 0.5  # AI的回答温度，值越高，回答越随机


# 定义请求模型
class ImageAnalysisRequest(BaseModel):
    prompt: str
    images_base64: str


class AIGenerateRequest(BaseModel):
    messages: list
    temperature: float


@app.get("/log/{log_class}/{error_level}/{message}")
async def log_via_http(log_class: str, error_level: str, message: str):
    log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{log_class}] [{error_level}] {message}\n"
    with open("log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)
    return {"message": "Logged via HTTP"}


@app.post("/analyze_image")
async def analyze_image(request: ImageAnalysisRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key is not set.")

    # 准备要发送到 OpenAI 的请求数据
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": request.prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{request.images_base64}",
                    },
                },
            ],
        }
    ]

    # 向 OpenAI API 发送请求
    analysis_result = get_answer_from_ai(messages)
    return {"analysis_result": analysis_result}


@app.post("/aigenerate")
async def analyze_image(request: AIGenerateRequest):
    global AI_TEMPERATURE
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key is not set.")
    # 准备要发送到 OpenAI 的请求数据
    messages = request.messages
    temperature = request.temperature
    if temperature:
        AI_TEMPERATURE = temperature
    # 向 OpenAI API 发送请求
    analysis_result = get_answer_from_ai(messages)
    return {"analysis_result": analysis_result}


def get_answer_from_ai(messages):
    global AI_TEMPERATURE
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, temperature=AI_TEMPERATURE
    )
    print("AI_TEMPERATURE:" + str(AI_TEMPERATURE))
    AI_TEMPERATURE = 0.5
    return response.choices[0].message.content


if __name__ == "__main__":
    # 使用uvicorn启动服务器，监听在0.0.0.0的8000端口
    uvicorn.run(app, host="0.0.0.0", port=8000)
