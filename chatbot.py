from common import client, makeup_response
import math
from memory_manager import MemoryManager
from function_calling import FunctionCalling, func_specs
from common import model, currTime

func_calling = FunctionCalling(model=model.basic)

class Chatbot:
    
    def __init__(self, model, system_role, instruction, **kwargs):
        self.context = [{"role": "system", "content": system_role}]
        self.model = model
        self.instruction = instruction
        self.max_token_size = 16 * 1024
        self.available_token_rate = 0.9
        self.user = kwargs["user"]
        self.assistant = kwargs["assistant"]
        self.memoryManager = MemoryManager()
        self.context.extend(self.memoryManager.restore_chat())

    def add_user_message(self, user_message):
        self.context.append({"role": "user", "content": user_message, "saved":False})


    
    def _send_request(self):
        analyzed_dict = func_calling.analyze(self.context[-1]['content'], func_specs) # self.context[-1]['content'] = user_message
        if analyzed_dict.get("function_call"): # 단일 함수 호출
            response = func_calling.run(analyzed_dict, self.context[:]) # 단일 함수 호출
        else:
            try:
                response = client.chat.completions.create(
                    model=self.model, 
                    messages=self.to_openai_contenxt(),
                    temperature=0.5,
                    top_p=1,
                    max_tokens=256,
                    frequency_penalty=0,
                    presence_penalty=0
                ).model_dump()
            except Exception as e:
                print(f"Exception 오류({type(e)}) 발생:{e}")
                if 'maximum context length' in str(e):
                    self.context.pop()
                    return makeup_response("메시지 조금 짧게 보내줄래?")
                else:
                    return makeup_response("[내 찐친 챗봇에 문제가 발생했습니다. 잠시 뒤 이용해주세요]")
        return response

    def send_request(self):
        self.context[-1]['content'] += self.instruction
        return self._send_request()
    

    def add_response(self, response):
        response_message = {
                "role" : response['choices'][0]['message']["role"],
                "content" : response['choices'][0]['message']["content"],
                "saved" : False
        }
        self.context.append(response_message)

    def get_response_content(self):
        return self.context[-1]['content']

    def clean_context(self):
        for idx in reversed(range(len(self.context))):
            if self.context[idx]["role"] == "user":
                self.context[idx]["content"] = self.context[idx]["content"].split("instruction:\n")[0].strip()
                break
    
    def handle_token_limit(self, response):
        # 누적 토큰 수가 임계점을 넘지 않도록 제어한다.
        try:
            current_usage_rate = response['usage']['total_tokens'] / self.max_token_size
            exceeded_token_rate = current_usage_rate - self.available_token_rate
            if exceeded_token_rate > 0:
                remove_size = math.ceil(len(self.context) / 10)
                self.context = [self.context[0]] + self.context[remove_size+1:]
        except Exception as e:
            print(f"handle_token_limit exception:{e}")
    
    def to_openai_contenxt(self):
        return [{"role":v["role"], "content":v["content"]} for v in self.context]
    
    def save_chat(self):
        self.memoryManager.save_chat(self.context)            