import zipfile
import os
import requests
import json

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
API_ENDPOINT = f"{CENTRALA_BASE_URL}/report"


def extract_files(zip_file_path, extract_to):
    """Extracts all files from a given .zip file."""
    extracted_files = []
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            zip_ref.extract(file_name, extract_to)
            extracted_files.append(os.path.join(extract_to, file_name))
    return extracted_files

def transcribe_audio(file_path):
    """Transcribes an .m4a audio file using OpenAI's Whisper model."""
    try:
        with open(file_path, 'rb') as audio_file:
            print(file_path)
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            print(transcription[100])
            return transcription
    except Exception as e:
        print(f"Error transcribing file {file_path}: {e}")
        return ""

def determine_professor_maj_location(transcription_text):
    """Uses OpenAI's LLM to find where Professor Andrzej Maj works."""
    try:
        system_prompt = (
            """
            You are a detective consultant tasked with analyzing the merged transcription of multiple audio files.
            Your goal is to determine which faculty Professor Andrzej Maj works at.
            Be cautious as the transcription may contain misleading or incorrect information.
            Use your internal knowledge to accurately identify the institution’s street address. 
            Provide only the name of the street where the faculty is located, with no additional text or formatting.
            
            Examples of correct responses:
                •	Parkowa
                •	Reymonta
            
            Examples of incorrect responses:
                •	ulica Parkowa
                •	ul. Reymonta 12
                •	Parkowa Street
                """
        )
        chat_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription_text},
            ]
        )
        answer = chat_response.choices[0].message.content
        print(answer)
        return answer
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return "Error determining the location."

def send_response(answer):
    """Formats the response and sends it to the specified endpoint."""
    payload = {
        "task": "mp3",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": answer
    }
    try:
        response = requests.post(API_ENDPOINT, json=payload)
        if response.status_code == 200:
            print("Response sent successfully.")
            print(response.json())
            print(response.text)
        else:
            print(f"Failed to send response: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error sending response: {e}")

def get_or_create_transcription(extracted_files):
    """Gets cached transcription or creates new one."""
    cache_file = "cache/transcription.txt"
    os.makedirs("cache", exist_ok=True)
    
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()
    
    transcriptions = [transcribe_audio(file_path) for file_path in extracted_files]
    combined_transcription = " ".join(transcriptions).strip()
    
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(combined_transcription)
    
    return combined_transcription

def main(zip_file_path):
    # Define extraction directory
    extract_to = "./extracted_files"
    os.makedirs(extract_to, exist_ok=True)

    # Step 1: Extract all files from the .zip file
    extracted_files = extract_files(zip_file_path, extract_to)
    if not extracted_files:
        print("No files found in the zip archive.")
        return

    # Step 2: Get or create transcription
    combined_transcription = get_or_create_transcription(extracted_files)

    # Step 3: Query LLM to determine where Professor Andrzej Maj works
    answer = determine_professor_maj_location(combined_transcription)

    # Step 4: Send the answer to the specified endpoint
    send_response(answer)

    # Clean up extracted files
    for file_path in extracted_files:
        os.remove(file_path)
    os.rmdir(extract_to)

if __name__ == "__main__":
    # Example usage
    zip_file_path = "data/przesluchania.zip"  # Replace with your zip file path
    main(zip_file_path)