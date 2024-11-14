import requests
import json
import logging
import os

import ollama
from dotenv import load_dotenv

load_dotenv()

AIDEVS_MY_APIKEY = os.getenv("AIDEVS_MY_APIKEY")
CENTRALA_BASE_URL = os.getenv("CENTRALA_BASE_URL")
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

        system_prompt = """
        You are preparing a training data for a college course.
        You are to replace all full names, addresses, names of cities, and age values in the following 
        text entirely with 'CENZURA.' Partial replacements are not allowed. 
        Preserve the original format, punctuation, and structure.
        <examples>
        USER: "Tożsamość osoby podejrzanej: Piotr Lewandowski. Zamieszkały w Łodzi przy ul. Wspólnej 22. Ma 34 lata."
        AI: "Tożsamość osoby podejrzanej: CENZURA. Zamieszkały w CENZURA przy ul. CENZURA. Ma CENZURA lata."
        
        USER: "Dane osoby podejrzanej: Paweł Zieliński. Zamieszkały w Warszawie na ulicy Pięknej 5. Ma 28 lat."
        AI: "Dane osoby podejrzanej: CENZURA. Zamieszkały w CENZURA na ulicy CENZURA. Ma CENZURA lat."
        
        USER: "Podejrzany nazywa się Tomasz Kaczmarek. Jest zameldowany w Poznaniu, ul. Konwaliowa 18. Ma 25 lat."
        AI: "Podejrzany nazywa się CENZURA. Jest zameldowany w CENZURA, ul. CENZURA. Ma CENZURA lat."
        
        USER: "Kontakt z podejrzanym Adam Kowalski: mieszka w Krakowie, ul. Piwna 10, ma 40 lat."
        AI: "Kontakt z podejrzanym CENZURA: mieszka w CENZURA, ul. CENZURA, ma CENZURA lat."
        
        USER: "Podejrzany Marek Nowak z ulicy Chopina 25, Poznań, lat 32."
        AI: "Podejrzany CENZURA z ulicy CENZURA, CENZURA, lat CENZURA."
        
        </examples>
        
        """
        # Prepare the messages for the model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]

        # Call the OpenAI API
        chat_response = ollama.chat(
            model="llama3.1",
            messages=messages,
        )

        # Get the processed text
        processed_text = chat_response['message']['content']
        print(processed_text)
        if processed_text.startswith("Sorry"):
            exit()

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
