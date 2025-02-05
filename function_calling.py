from common import client, model, makeup_response 
import json
import requests
from pprint import pprint
from tavily import TavilyClient
import os

# Tavily API 클라이언트 설정
tavily = TavilyClient(api_key='')

# 화폐 코드
global_currency_code = {'달러':'USD','엔화':'JPY','유로화':'EUR','위안화':'CNY','파운드':'GBP'}

def get_celsius_temperature(**kwargs):
    location = kwargs['location']
    
    # Tavily 검색을 통해 날씨 데이터 가져오기
    search_query = f"{location} 현재 날씨 섭씨"
    response = tavily.search(query=search_query, include_answer=True)['answer']
    
    print("검색된 날씨 데이터:", response)
    return response

def get_currency(**kwargs):    
    currency_name = kwargs['currency_name']
    currency_name = currency_name.replace("환율", "")
    currency_code = global_currency_code.get(currency_name, 'USD')
    
    # Tavily 검색을 통해 환율 데이터 가져오기
    search_query = f"{currency_code} 원화 환율"
    response = tavily.search(query=search_query, include_answer=True)['answer']
    
    print("검색된 환율 데이터:", response)
    return response

def search_internet(**kwargs):
    print("search_internet", kwargs)
    answer = tavily.search(query=kwargs['search_query'], include_answer=True)['answer']
    print("answer:", answer)
    return answer

func_specs = [
    {
        "name": "get_celsius_temperature",
        "description": "지정된 위치의 현재 섭씨 날씨 확인",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "광역시도, e.g. 서울, 경기",
                }
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_currency",
        "description": "지정된 통화의 원(KRW) 기준의 환율 확인.",
        "parameters": {
            "type": "object",
            "properties": {
                "currency_name": {
                    "type": "string",
                    "description": "통화명, e.g. 달러환율, 엔화환율",
                }
            },
            "required": ["currency_name"],
        },
    },
    {
        "name": "search_internet",
        "description": "답변 시 인터넷 검색이 필요하다고 판단되는 경우 수행",
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "인터넷 검색을 위한 검색어",
                }
            },
            "required": ["search_query"],
        }
    }
]

class FunctionCalling:

    def __init__(self, model):
        self.available_functions = {
            "get_celsius_temperature": get_celsius_temperature,
            "get_currency": get_currency,
            "search_internet": search_internet,
        }
        self.model = model

    def analyze(self, user_message, func_specs):
        try:
            response = client.chat.completions.create(
                model=model.basic,
                messages=[{"role": "user", "content": user_message}],
                functions=func_specs,
                function_call="auto", 
            )
            message = response.choices[0].message
            message_dict = message.model_dump() 
            pprint(("message_dict=>", message_dict))
            return message_dict
        except Exception as e:
            print("Error occurred(analyze):", e)
            return makeup_response("[analyze 오류입니다]")
    
    def run(self, analyzed_dict, context):
        func_name = analyzed_dict["function_call"]["name"]
        func_to_call = self.available_functions[func_name]
        try:
            func_args = json.loads(analyzed_dict["function_call"]["arguments"])
            # 챗GPT가 알려주는 매개변수명과 값을 입력값으로하여 실제 함수를 호출한다.
            func_response = func_to_call(**func_args)
            context.append({
                "role": "function", 
                "name": func_name, 
                "content": str(func_response)
            })
            return client.chat.completions.create(model=self.model, messages=context).model_dump()            
        except Exception as e:
            print("Error occurred(run):", e)
            return makeup_response("[run 오류입니다]")
