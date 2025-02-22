import os
from openai import OpenAI
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class Model: 
    basic: str = "gpt-4o-mini"
    advanced: str = "gpt-4o"
        
api_key = ''

model = Model();    
client = OpenAI(api_key=api_key, timeout=30, max_retries=1)
        
def makeup_response(message, finish_reason="ERROR"):
    return {
                "choices": [
                    {
                        "finish_reason": finish_reason,
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": message
                        }                   
                    }
                ],
                "usage": {"total_tokens": 0},
            }
                
def today():
    korea = pytz.timezone('Asia/Seoul')# 한국 시간대를 얻습니다.
    now = datetime.now(korea)# 현재 시각을 얻습니다.
    return(now.strftime("%Y%m%d"))# 시각을 원하는 형식의 문자열로 변환합니다.

def yesterday():    
    korea = pytz.timezone('Asia/Seoul')# 한국 시간대를 얻습니다.
    now = datetime.now(korea)# 현재 시각을 얻습니다.
    one_day = timedelta(days=1)    # 하루 (1일)를 나타내는 timedelta 객체를 생성합니다.
    yesterday = now - one_day # 현재 날짜에서 하루를 빼서 어제의 날짜를 구합니다.
    return yesterday.strftime('%Y%m%d') # 어제의 날짜를 yyyymmdd 형식으로 변환합니다.

def currTime():
    # 한국 시간대를 얻습니다.
    korea = pytz.timezone('Asia/Seoul')
    # 현재 시각을 얻습니다.
    now = datetime.now(korea)
    # 시각을 원하는 형식의 문자열로 변환합니다.
    formatted_now = now.strftime("%Y.%m.%d %H:%M:%S")
    return(formatted_now)