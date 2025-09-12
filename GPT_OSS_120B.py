import requests
import os
import dotenv

def call_llm(api_key,  user_prompt, system_prompt):
    url = "https://mkp-api.fptcloud.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-oss-120b",
        "messages": [
            {   "role": "system", "content": f"{system_prompt}",
                "role": "user", "content": f"{user_prompt}"}
        ],
        "max_tokens": 4096,
        "temperature": 0.1,
        "frequency_penalty": 0.5
    }

    response = requests.post(url, headers=headers, json=data)

    print("Status code:", response.status_code)
    data = response.json()
    return data['choices'][0]['message']['content']

if __name__ == "__main__":
    dotenv.load_dotenv()
    api_key = os.getenv('FPT_120B')
    if api_key:
        print("Get api key successfully")
    else:
        raise Exception("API key does not exist")
    print(call_llm(api_key, "Print a question mark", "Do not care about this"))