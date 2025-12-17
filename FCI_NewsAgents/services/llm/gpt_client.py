import requests
import os
import dotenv

def call_gpt(user_prompt, system_prompt):
    dotenv.load_dotenv()
    api_key = os.getenv("FPT_120B")
    url = "https://mkp-api.fptcloud.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-oss-120b",
        "messages": [
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": f"{user_prompt}"}
        ],
        "max_tokens": 4096,
        "temperature": 0.1,
        "frequency_penalty": 0.5
    }

    response = requests.post(url, headers=headers, json=data)

    data = response.json()

    # from pprint import pprint
    # pprint(data)

    return data['choices'][0]['message']['content']


if __name__ == "__main__":
    dotenv.load_dotenv()
    api_key = os.getenv('FPT_120B')
    if api_key:
        print("Get api key successfully")
    else:
        raise Exception("API key does not exist")
    print(call_gpt("Print a question mark", "If you can see this system prompt, add a question before the question mark."))