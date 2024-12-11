import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests

from utils import post_json_data_to_url


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION_ID")
CENTRALA_BASE_URL = os.getenv("CENTRALA_BASE_URL")
AIDEVS_MY_APIKEY = os.getenv("AIDEVS_MY_APIKEY")

questions = {
    "01": "Do którego roku przeniósł się Rafał",
    "02": "Kto wpadł na pomysł, aby Rafał przeniósł się w czasie?",
    "03": "Gdzie znalazł schronienie Rafał? Nazwij krótko to miejsce",
    "04": "Którego dnia Rafał ma spotkanie z Andrzejem? (format: YYYY-MM-DD)",
    "05": "Gdzie się chce dostać Rafał po spotkaniu z Andrzejem?"
}

answers = {
  "01": "2019",
  "02": "Adam",
  "03": "jaskinia",
  "04": "2024-11-12",
  "05": "Lubawa"
}

print("\nAll answers:", answers)

final_payload = {
    "task": "notes",
    "apikey": AIDEVS_MY_APIKEY,
    "answer": answers
}
final_response = post_json_data_to_url(final_payload, f"{CENTRALA_BASE_URL}/report")