import os
from typing import Literal

import dotenv
import requests


def call_gpt(user_prompt, system_prompt, model: Literal["gpt-oss-20b", "gpt-oss-120b"] = "gpt-oss-120b"):
    """
    Make a call to FPT's GPT-OSS model.

    Args:
        user_prompt (str): The prompt provided by the user.
        system_prompt (str): The system-level instructions for the model.
        model (str): The model to use, either "gpt-oss-20b" or "gpt-oss-120b".

    Returns:
        str: The response from the GPT model.
    """
    dotenv.load_dotenv()
    api_key = os.getenv("FPT_120B")
    url = "https://mkp-api.fptcloud.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": f"{user_prompt}"}
        ],
        "max_tokens": 8192,
        "temperature": 0.1,
        "frequency_penalty": 0.5
    }

    response = requests.post(url, headers=headers, json=data)

    data = response.json()

    try:
        return data['choices'][0]['message']['content']
    except KeyError:
        raise Exception(f"Error from GPT API: {data}")


if __name__ == "__main__":
    dotenv.load_dotenv()
    api_key = os.getenv('FPT_120B')
    if api_key:
        print("Get api key successfully")
    else:
        raise Exception("API key does not exist")
    print(call_gpt("Print a question mark", "If you can see this system prompt, add a question before the question mark."))