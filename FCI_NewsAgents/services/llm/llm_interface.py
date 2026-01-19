import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from typing import Literal

from FCI_NewsAgents.services.llm.gpt_client import call_gpt


def call_llm(
    user_prompt: str, 
    system_prompt: str,
    model: Literal["gpt-oss-20b", "gpt-oss-120b"] = "gpt-oss-120b",
    max_tokens: int = 8192,
) -> str:
    """
    A unified interface to call different LLM models. Currently supporting 2 models: "gpt-oss-20b" and "gpt-oss-120b".

    Currently, the `max_tokens` parameter for each model is as follows (you can set anywhere below it):
    - GPT-OSS-120B models: up to 128K tokens
    - GPT-OSS-20B models: up to 128K tokens

    Args:
        user_prompt (str): The prompt provided by the user.
        system_prompt (str): The system-level instructions for the model.
        model (Literal["gpt-oss-20b", "gpt-oss-120b"]): The specific model to use within the chosen provider.
        max_tokens (int): The maximum number of tokens to generate. Defaults to 8192.

    Returns:
        str: The response from the selected LLM model.
    """
    return call_gpt(user_prompt, system_prompt, model, max_tokens)
    
if __name__ == "__main__":
    user_prompt = "Print a question mark"
    system_prompt = "If you can see this, add a question before the question mark, the final result will be the question + question mark"
    print(call_llm(user_prompt, system_prompt))