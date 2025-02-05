from common import client, model, makeup_response
import json
import requests
from pprint import pprint
import os

# Bing Search API 키 설정
BING_API_KEY = os.getenv("BING_API_KEY")

class FunctionCalling:

    def __init__(self, model):
        self.available_functions = {
            "search_internet": self.bing_web_search,
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
        func_to_call = self.available_functions.get(func_name)
        if not func_to_call:
            return makeup_response("[지원하지 않는 기능입니다]")
        try:
            func_args = json.loads(analyzed_dict["function_call"]["arguments"])
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

    def bing_web_search(self, **kwargs):
        """Bing Web Search API를 사용하여 웹 검색을 수행하고 결과를 반환합니다."""
        query = kwargs['search_query']
        headers = {'Ocp-Apim-Subscription-Key': BING_API_KEY}
        params = {'q': query, 'textDecorations': True, 'textFormat': 'HTML', 'count': 10}
        search_url = "https://api.bing.microsoft.com/v7.0/search"
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()  # 오류가 발생하면 예외를 발생시킵니다.
        search_results = response.json()
        return search_results  # 검색 결과 전체를 반환합니다.