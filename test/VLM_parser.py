from PIL import Image
import requests
import torch
# Load model directly
from transformers import AutoProcessor, AutoModelForImageTextToText

processor = AutoProcessor.from_pretrained("google/gemma-3-4b-it")
model = AutoModelForImageTextToText.from_pretrained("google/gemma-3-4b-it")
def get_message(image_url):
    '''Given an image url, get the corresponding message for the VLM to process'''
    image = Image.open(image_url)
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are an image parser assistant, your mission is to process the input image then generates the key summarization, the important information from the input image, the output should be concise"}]
        },
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},                
            ]
        }
    ]
    return messages
messages = get_message(r"C:\Users\ADMIN\AI-Agents---FCI-Internship-2025-Summer\res.jpg")


inputs = processor.apply_chat_template(
	messages,
	add_generation_prompt=True,
	tokenize=True,
	return_dict=True,
	return_tensors="pt",
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=40)
print(processor.decode(outputs[0][inputs["input_ids"].shape[-1]:]))

