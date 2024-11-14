import requests
import json
import logging
import os

from openai import OpenAI
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION_ID")
AIDEVS_MY_APIKEY = os.getenv("AIDEVS_MY_APIKEY")
CENTRALA_BASE_URL = os.getenv("CENTRALA_BASE_URL")
openai_client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)


# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    # URL of the text file
    url = f"{CENTRALA_BASE_URL}/data/{AIDEVS_MY_APIKEY}/robotid.json"

    # Download the text file
    response = requests.get(url)

    robot_desc = response.json()['description']

    prompt = f"Create an image of a robot based on the following description: {robot_desc}"

    # Call the OpenAI API
    chat_response = openai_client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = chat_response.data[0].url

    # Print the processed text
    print(image_url)

    # Prepare the JSON payload
    payload = {
        "task": "robotid",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": image_url
    }

    # Submit the processed output
    submit_url = f"{CENTRALA_BASE_URL}/report"
    headers = {'Content-Type': 'application/json'}
    submission_response = requests.post(submit_url, json=payload, headers=headers)

    if submission_response.status_code == 200:
        logging.info("Submission successful.")
        logging.info(submission_response.json())
        logging.info(submission_response.text)
    else:
        logging.error(f" Submission failed. Status code: {submission_response.status_code}")
        logging.error(f" submission_response.text")


if __name__ == "__main__":
    main()
