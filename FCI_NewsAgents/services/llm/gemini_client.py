import os

import dotenv
import google.generativeai as genai


def call_gemini(user_prompt: str, system_prompt: str, model: str = "gemini-2.5-flash"):
    """
    Make a call to Google's Gemini model.

    Args:
        user_prompt (str): The prompt provided by the user.
        system_prompt (str): The system-level instructions for the model.
        model (str): The specific Gemini model to use.

    Returns:
        str: The response from the Gemini model.
    """
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