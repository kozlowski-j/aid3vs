import json
import os
from dotenv import load_dotenv
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

def generate_message(sample: str, is_correct: bool) -> str:
    return json.dumps({
        "messages":[
            {"role": "system", "content": "Decide if sample is correct"},
            {"role": "user", "content": sample},
            {"role": "assistant", "content": str(is_correct)}  
        ]
    })


def prepare_training_data(input_file_path: str, output_file_path: str, is_correct: bool):
    with open(input_file_path, 'r') as input_file:
        with open(output_file_path, 'a') as output_file:
            for line in input_file:
                json_line = generate_message(line.strip(), is_correct)
                output_file.write(json_line + '\n')


def assess_data(model_name: str, content: str):
    response = openai_client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "Decide if sample is correct",
            },
            {
                "role": "user",
                "content": content,
            },
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


if __name__ == '__main__':
    prepare_training_data(
        input_file_path="data/lab_data/correct.txt",
        output_file_path="data/lab_data/training_dataset.jsonl",
        is_correct=True
    )

    prepare_training_data(
        input_file_path="data/lab_data/incorrect.txt",
        output_file_path="data/lab_data/training_dataset.jsonl",
        is_correct=False
    )

    fine_tuned_model_name = "ft:gpt-4o-mini-2024-07-18:personal:s04e02:AbK0wMQY"

    results = []
    with open("data/lab_data/verify.txt", 'r') as verify_file:
        for line in verify_file:
            line_id, content = line.strip().split('=')
            result = assess_data(fine_tuned_model_name, content)
            if result.lower() == 'true':
                print(line_id)
                results.append(result)

    final_payload = {
        "task": "research",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": results
    }
    final_response = post_json_data_to_url(final_payload, f"{CENTRALA_BASE_URL}/report")




