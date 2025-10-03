import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from FCI_NewsAgents.services.llm.gemini_client import call_gemini
from FCI_NewsAgents.services.llm.gpt_client import call_gpt

def call_llm(user_prompt, system_prompt, model_used:str = "gemini", gemini_model:str = "gemini-2.5-flash") -> str:
    if model_used == "gemini":
        return call_gemini(user_prompt, system_prompt, gemini_model)
    elif model_used == "gpt":
        return call_gpt(user_prompt, system_prompt)
    else:
        print("The model_used parameter should be gemini or gpt. Currently using gemini by default")
        return call_gemini(user_prompt, system_prompt, gemini_model)
if __name__ == "__main__":
    user_prompt = "Print a question mark"
    system_prompt = "If you can see this, add a question before the question mark, the final result will be the question + question mark"
    print(call_llm(user_prompt, system_prompt))