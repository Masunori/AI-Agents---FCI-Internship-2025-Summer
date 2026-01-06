import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from typing import Literal

from FCI_NewsAgents.services.llm.gemini_client import call_gemini
from FCI_NewsAgents.services.llm.gpt_client import call_gpt


def call_llm(
    user_prompt: str, 
    system_prompt: str, 
    model_used: Literal["gemini", "gpt"] = "gemini", 
    model: str = "gemini-2.5-flash"
) -> str:
    """
    A unified interface to call different LLM models.

    The user has to make sure that the `model` parameter corresponds to the `model_used` parameter.
    - If `model_used` is `gpt`, then `model` should be either "gpt-oss-20b" or "gpt-oss-120b".
    - If `model_used` is `gemini`, then `model` should be a valid Gemini model name like "gemini-2.5-flash".

    Args:
        user_prompt (str): The prompt provided by the user.
        system_prompt (str): The system-level instructions for the model.
        model_used (str): The model provider to use, either "gemini" or "gpt".
        model (str): The specific model to use within the chosen provider.

    Returns:
        str: The response from the selected LLM model.
    """
    if model_used == "gemini":
        return call_gemini(user_prompt, system_prompt, model)
    elif model_used == "gpt":
        return call_gpt(user_prompt, system_prompt, model)
    else:
        print("The model_used parameter should be gemini or gpt. Currently using gemini by default")
        return call_gemini(user_prompt, system_prompt, model)
    
if __name__ == "__main__":
    user_prompt = "Print a question mark"
    system_prompt = "If you can see this, add a question before the question mark, the final result will be the question + question mark"
    print(call_llm(user_prompt, system_prompt))