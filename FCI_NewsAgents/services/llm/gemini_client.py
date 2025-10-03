import os
import dotenv
import google.generativeai as genai
def call_gemini(user_prompt,system_prompt, model = "gemini-2.5-flash"):
    dotenv.load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key= api_key)
    model = genai.GenerativeModel(
        model_name= model,
        system_instruction=system_prompt
    )
    response = model.generate_content(user_prompt)
    return response.text

if __name__ == "__main__":
    user_prompt = "Print a question mark"
    system_prompt = "If you can see this, add a question before the question mark the user ask you to print"
    print(call_gemini(user_prompt, system_prompt))