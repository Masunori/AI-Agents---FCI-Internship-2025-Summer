import os
import dotenv
import base64
dotenv.load_dotenv()
from mistralai import Mistral

api_key = os.getenv("mistral_ocr")

if api_key:
    print("API key for Mistral is available")
else:
    print("Provide API key for Mistral")

client = Mistral(api_key=api_key)

uploaded_file = client.files.upload(
    file = {
        "file_name": r"test\Group 10.pdf",
        "content": open(r"test\Group 10.pdf", "rb")
    },
    purpose="ocr"
)

file_url = client.files.get_signed_url(file_id=uploaded_file.id)

response = client.ocr.process(
    model = "mistral-ocr-latest",
    document= {
        "type": "document_url",
        "document_url": file_url.url
    },
    include_image_base64= True
)

def data_url_to_bytes(data_url):
    _, enocoded = data_url.split(",", 1)
    return base64.b64decode(enocoded)

def export_image(image):
    parsed_image = data_url_to_bytes(image.image_base64)
    with open(image.id, 'wb') as file:
        file.write(parsed_image)


print(response.pages[0].markdown)
# with open('output.md', 'w') as f:
#     for page in response.pages:
#         f.write(page.markdown)
#         for image in page.images:
#             export_image(image)