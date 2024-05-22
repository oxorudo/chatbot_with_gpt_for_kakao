from flask import Flask, render_template, request
import sys
from common import model, currTime
from chatbot import Chatbot
from characters import system_role, instruction
from concurrent.futures import ThreadPoolExecutor
import requests
import concurrent
from function_calling import FunctionCalling, func_specs
import atexit


#jjinchin 인스턴스 생성
jjinchin = Chatbot(
    model = model.basic,
    system_role = system_role,
    instruction = instruction,
    user = "태경",
    assistant = "고비"
)

application = Flask(__name__)

func_calling = FunctionCalling(model=model.basic)

@application.route("/")
def hello():
    return "Hello goorm!" 

def format_response(resp, useCallback=False):
    data = {
            "version": "2.0",
            "useCallback": useCallback,
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": resp
                        }
                    }
                ]
            }
        }
    return data

executor = ThreadPoolExecutor(max_workers=1)


# 비동기 호출 개선 전 코드

def async_send_request(chat_gpt, user_message, callbackUrl):
    chat_gpt.add_user_message(user_message)
    # 챗GPT에게 함수사양을 토대로 사용자 메시지에 호응하는 함수 정보를 분석해달라고 요청
    analyzed_dict = func_calling.analyze(user_message, func_specs) # 단일 함수 호출
    #analyzed, analyzed_dict = func_calling.analyze(request_message, tools) # 병렬적 함수 호춝 
    # 챗GPT가 함수 호출이 필요하다고 분석했는지 여부 체크
    if analyzed_dict.get("function_call"): # 단일 함수 호출
    #if analyzed_dict.get("tool_calls"): # 병렬적 함수 호출
        # 챗GPT가 분석해준 대로 함수 호출
        response = func_calling.run(analyzed_dict, jjinchin.context[:]) # 단일 함수 호출
        #response = func_calling.run(analyzed, analyzed_dict, jjinchin.context[:]) # 병렬적 함수 호출
        jjinchin.add_response(response)
    else:
        response = jjinchin.send_request()
        jjinchin.add_response(response)
    response_message = chat_gpt.get_response_content()
    print("response_message:", response_message)
    chat_gpt.handle_token_limit(response)
    chat_gpt.clean_context()    
    response_to_kakao = format_response(response_message, useCallback=False)
    callbackResponse = requests.post(callbackUrl, json=response_to_kakao)
    print("CallbackResponse:", callbackResponse.text)
    print(f"{'-'*50}\n{currTime()} requests.post 완료\n{'-'*50}")

@application.route('/chat-kakao', methods=['POST'])
def chat_kakao():
    print(f"{'-'*50}\n{currTime()} chat-kakao 시작\n{'-'*50}")
    print("request.json:", request.json)
    request_message = request.json['userRequest']['utterance']
    callbackUrl = request.json['userRequest']['callbackUrl']    
    executor.submit(async_send_request, jjinchin, request_message, callbackUrl)
    immediate_response = format_response("", useCallback=True)
    print("immediate_response",immediate_response)
    return immediate_response

@atexit.register
def shutdown():
    print("flask shutting down...")
    jjinchin.save_chat()


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=int(sys.argv[1]))
