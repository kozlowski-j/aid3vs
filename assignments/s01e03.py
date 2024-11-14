import json
import os

import requests
from openai import OpenAI
from dotenv import load_dotenv
from utils import verify_json

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION_ID")
POLIGON_BASE_URL = os.getenv("POLIGON_BASE_URL")
openai_client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)

with open('assignments/data/s01e03_data.json', 'r') as file:
    data_dict = json.load(file)

test_data = data_dict['test-data']
test_data_fixed = []

for i in test_data:
    fixed_test_object = {
        "question": i['question'],
        "answer": eval(i['question'])
    }

    if "test" in i.keys():
        chat_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Answer the question using minimum number of words possible."},
                {"role": "user", "content": i["test"]["q"]},
            ]
        )
        fixed_a = chat_response.choices[0].message.content

        fixed_test_object["test"] = {
            "q": i["test"]["q"],
            "a": fixed_a
        }
    test_data_fixed.append(fixed_test_object)

data_dict_fixed = data_dict.copy()
data_dict_fixed['test-data'] = test_data_fixed

verified_json = verify_json(data_dict_fixed)

with open("assignments/data/s01e03_data_fixed.json", 'w') as file:
    json.dump(data_dict_fixed, file, indent=4)

# Define the API endpoint
verify_url = f"{POLIGON_BASE_URL}/verify"

# Define the JSON payload
payload = {
    "task": "JSON",
    "apikey": os.getenv("AIDEVS_API_KEY"),
    "answer": verified_json
}

# Send the POST request
response = requests.post(verify_url, data=json.dumps(payload))

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    response_data = response.json()
    print('Response:', response_data)
else:
    print('Failed to send request:', response.status_code, response.text)



