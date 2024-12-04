import json

import re
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI

from utils import post_json_data_to_url


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION_ID")
CENTRALA_BASE_URL = os.getenv("CENTRALA_BASE_URL")
AIDEVS_MY_APIKEY = os.getenv("AIDEVS_MY_APIKEY")

data_path = "assignments/data"

openai_client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)

if not os.path.exists(f"{data_path}/start_response.txt"):
    start_payload = {
        "task": "photos",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": "START"
    }
    print(f"payload: {start_payload}")
    start_response = post_json_data_to_url(start_payload, f"{CENTRALA_BASE_URL}/report")
    print(f"start_response: {start_response}")
    with open(f"{data_path}/start_response.txt", "w") as f:
        f.write(start_response.text)
else:
    with open(f"{data_path}/start_response.txt", "r") as f:
        start_response = f.read()

print(f"start_response: {start_response}")  

PHOTOS_URL = "https://centrala.ag3nts.org/dane/barbara/"
photos_names = [
    "IMG_559.PNG",
    "IMG_1410.PNG",
    "IMG_1443.PNG",
    "IMG_1444.PNG",
]


def decide_how_to_fix_photo(photo_name: str, photos_url=PHOTOS_URL):
    photo_url = f"{photos_url}/{photo_name}"
    photo_fixer_prompt = """
    You are a photo analyzer. You are given a photo, and you need to decide if it presents a person. If the photo is damaged or unclear, you need to decide how to fix it. Make sure to make as few mistakes as possible when selecting the appropriate command.

    <prompt_objective>
    Analyze the photo and decide if it presents a person. If the photo is damaged or unclear, you need to decide how to fix it. 
    Provide thorough reasoning in the "_thinking" field.
    Always respond with a valid JSON object without markdown blocks.
    </prompt_objective>

    <prompt_rules>
    - **Commands you can use:** REPAIR, DARKEN, BRIGHTEN.
    - **Decision-making process:**
        1. Carefully analyze the image for clarity and quality.
        2. Evaluate if the image clearly shows a person.
        3. If adjustments are required, select the most suitable command with as few mistakes as possible.
    - **Command selection guidelines:**
        - If the photo is too dark, return the BRIGHTEN command, and FALSE in the is_person_clearly_visible field.
        - If the photo is too bright, return the DARKEN command, and FALSE in the is_person_clearly_visible field.
        - If the photo is damaged (e.g., corrupted, missing parts, blurred), return the REPAIR command, and FALSE in the is_person_clearly_visible field.
        - If the photo is clear and shows a person without requiring adjustments, return the `null` command, and TRUE in the is_person_clearly_visible field.
    - Always prioritize accuracy when deciding the command to minimize errors.
    - In case of ambiguity or conflicting indicators, provide detailed reasoning in the "_thinking" field to justify your choice.
    </prompt_rules>

    <output_format>
    Always respond with this JSON structure:
    {
        "_thinking": "Detailed explanation of your interpretation process, consideration of options, reasoning for decisions, and any assumptions made.",
        "command": "REPAIR, DARKEN, BRIGHTEN, or null",
        "is_person_clearly_visible": true or false
    }
    </output_format>
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": photo_fixer_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": photo_url,
                        },
                    },
                ],  
            },
        ],
        max_tokens=300,
    )
    decision_response = response.choices[0].message.content.strip()
    print(f"decision_response: {decision_response}")
    decision_response_json = json.loads(decision_response)
    decision_command = decision_response_json.get("command")
    decision_is_person_clearly_visible = decision_response_json.get("is_person_clearly_visible")

    print(f"decision_command: {decision_command}")
    print(f"decision_is_person_clearly_visible: {decision_is_person_clearly_visible}")

    return decision_command, decision_is_person_clearly_visible


def fix_photo(photo_name: str, command: str):
    payload = {
        "task": "photos",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": f"{command.upper()} {photo_name.upper()}"
    }
    fix_response = post_json_data_to_url(payload, f"{CENTRALA_BASE_URL}/report")
    fix_response_txt = fix_response.json()['message']
    return fix_response_txt


def extract_image_name(text: str) -> str:   
    pattern = r'IMG_[A-Z0-9_]+\.PNG'
    match = re.search(pattern, text)
    
    if match:
        return match.group(0)
    return ""


clean_photos_names = []

for photo_name in photos_names:
    print(f"Processing photo: {photo_name}")
    new_photo_name = photo_name

    i = 0
    while i < 5:
        print(i, new_photo_name)
        decision_command, decision_is_person_clearly_visible = decide_how_to_fix_photo(new_photo_name)

        if decision_is_person_clearly_visible or decision_is_person_clearly_visible == "true":
            print(f"Photo {new_photo_name} is clear and person is clearly visible.")
            clean_photos_names.append(new_photo_name)
            break
        else:
            print(f"Photo {new_photo_name} is not clear or person is not clearly visible.")
            fix_response = fix_photo(new_photo_name, decision_command)
            new_photo_name = extract_image_name(fix_response)
        i += 1

print(f"clean_photos_names: {clean_photos_names}")

# Describe the person visible in the photos
describe_person_prompt = """
You are a photo analyzer. You are given a few photos, and you need to describe the person visible in the photos.
Some of them may present the same person, but in different poses or with different background.
Some photos might be misleading, so describe only the person visible in most of them.
Pay attention to details and describe the person as accurately as possible.
Provide a detailed description of the person's appearance, including their facial features, hair, and specific marks.
Your answer must be in Polish.
"""

describe_person_query_content = [
    {"type": "text", "text": describe_person_prompt},
]

for photo_name in clean_photos_names:
    photo_url = f"{PHOTOS_URL}/{photo_name}"
    describe_person_query_content.append({
        "type": "image_url",
        "image_url": {
            "url": photo_url,
        },
    })

describe_person_response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": describe_person_query_content,  
        },
    ],
    max_tokens=500,
)
describe_person_response_txt = describe_person_response.choices[0].message.content.strip()
print(f"describe_person_response_txt: {describe_person_response_txt}")


final_payload = {
    "task": "photos",
    "apikey": AIDEVS_MY_APIKEY,
    "answer": describe_person_response_txt
}
final_response = post_json_data_to_url(final_payload, f"{CENTRALA_BASE_URL}/report")
