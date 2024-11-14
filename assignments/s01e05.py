import requests
import json
import logging
import os

from openai import OpenAI
from dotenv import load_dotenv
from utils import get_custom_response, verify_json

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
    url = f"{CENTRALA_BASE_URL}/data/{AIDEVS_MY_APIKEY}/cenzura.txt"

    try:
        # Download the text file
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"Failed to download the file. Status code: {response.status_code}")
            return

        text = response.text

        # Check if the file is empty or corrupted
        if not text.strip():
            logging.info("The downloaded text file is empty or corrupted. Terminating.")
            return

        # Prepare the messages for the model
        messages = [
            {"role": "system", "content": "You are to replace all full names, addresses, names of cities, and age values in the following text entirely with 'CENZURA.' Partial replacements are not allowed. Preserve the original format, punctuation, and structure."},
            {"role": "user", "content": text}
        ]

        # Call the OpenAI API
        chat_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
        )

        # Get the processed text
        processed_text = chat_response.choices[0].message.content

        # Print the processed text
        print(processed_text)

        # Prepare the JSON payload
        payload = {
            "task": "CENZURA",
            "apikey": AIDEVS_MY_APIKEY,
            "answer": processed_text
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

    except Exception as e:
        logging.error(f"An error occurred: {type(e).__name__}: {e}")
        return

if __name__ == "__main__":
    main()
