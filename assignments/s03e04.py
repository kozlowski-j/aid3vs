import json
from json import JSONDecodeError

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

openai_client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)


barbara_url = f"{CENTRALA_BASE_URL}/dane/barbara.txt"
barbara_response = requests.get(barbara_url)
note_about_barbara = barbara_response.text

def get_people_from_api(person_name: str):
    people_url = f"{CENTRALA_BASE_URL}/people"
    people_response = requests.get(people_url, json={
        "query": person_name,
        "apikey": AIDEVS_MY_APIKEY
    })
    return people_response.json()

def get_places_from_api(place_name: str):
    places_url = f"{CENTRALA_BASE_URL}/places"
    places_response = requests.get(places_url, json={
        "query": place_name,
        "apikey": AIDEVS_MY_APIKEY
    })
    return places_response.json()

def clean_name(name: str):
    name = name.upper()
    name = name.replace("Ł", "L")
    name = name.replace("Ó", "O")
    name = name.replace("Ś", "S")
    name = name.replace("Ż", "Z")
    name = name.replace("Ą", "A")
    name = name.replace("Ę", "E")
    name = name.replace("Ń", "N")
    name = name.replace("Ź", "Z")
    return name

def report_to_headquarters(answer: str):
    payload = {
        "task": "loop",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": answer
    }
    response = post_json_data_to_url(payload, f"{CENTRALA_BASE_URL}/report")
    return json.loads(response.text)["message"]


system_prompt = f"""
    You are a highly skilled detective specializing in locating people. 
    You are tasked with analyzing provided information and deciding on the best course of action to find BARBARA.

    ## Context

    A note about BARBARA was found:
    {note_about_barbara}

    ## Objective

    Your objective is to find the place where BARBARA is hiding.

    ## Instructions

    •	Use ALL available information in the context.
    •	Gather additional details if needed to narrow down BARBARA`s location.
    •	Ensure your reasoning aligns with the choice you make.
    •	Avoid any formatting other than plain JSON in your response.
    •   Focus on finding the place where BARBARA is hiding.
    •   AZAZEL is a valid name of a person.
    •   CIECHOCINEK and GRUDZIADZ are valid places names.
    •   Based on the provided context, carefully evaluate the information and determine the next step. 

    ## Choices

    1.	Request the people tool
    •	Use this to gather information about places a specific person visited.
    •	Provide the FIRST name of the person as the query.
    2.	Request the places tool
    •	Use this to gather information about people spotted in a specific place.
    •	Provide the name of the place as the query.
    3.	Request the report tool
    •	Use this to send a location to the headquarters for further investigation.
    •	Provide the name of the place as the query.

    ## Output Format

    Your response must be in the following JSON format:

    {{
        "thinking": "Explain your reasoning and the next steps to take.",
        "choice": "One of the choices from the list (people, places, or report).",
        "name": "The name of the person or place to query or report."
    }}

    ## Example Output

    {{
        "thinking": "I need to find where BARBARA is hiding by tracking her friend ANNA. I will start by requesting information about places visited by ANNA.",
        "choice": "people",
        "name": "ANNA"
    }}

    ## Remember: your objective is to find BARBARA.

"""


if __name__ == "__main__":
    user_prompt = "## NEW CONTEXT:"
    i = 0
    while i < 30:
        print(i)
        i += 1
        openai_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        try:
            ai_response = openai_response.choices[0].message.content.replace("```json", "").replace("```", "")
            ai_response = json.loads(ai_response)
        except JSONDecodeError as e:
            print(openai_response.choices[0].message.content)
            print(e)
            continue
        print(ai_response)
        ai_choice = ai_response["choice"]
        ai_provided_name = ai_response["name"]

        if ai_choice == "report":
            msg = report_to_headquarters(ai_provided_name)
            if msg.startswith("{{FLG"):
                print(msg)
                break
            else:
                new_context = f"\n- {ai_choice}: {ai_provided_name}, headquarters response: {msg}"
                if new_context not in user_prompt:
                    user_prompt += new_context
                else:
                    user_prompt += f"\nYOU ALREADY REQUESTED INFORMATION ABOUT {ai_provided_name} from tool `{ai_choice}`."
        elif ai_choice == "people":
            people_response = get_people_from_api(clean_name(ai_provided_name))
            new_context = f"\n- {ai_provided_name}: {people_response['message'].split(' ')}"
            if new_context not in user_prompt:
                user_prompt += new_context
            else:
                user_prompt += f"\nYOU ALREADY REQUESTED INFORMATION ABOUT {ai_provided_name} from tool `{ai_choice}`."
        elif ai_choice == "places":
            places_response = get_places_from_api(clean_name(ai_provided_name))
            new_context = f"\n- {ai_provided_name}: {places_response['message'].split(' ')}"
            if new_context not in user_prompt:
                user_prompt += new_context
            else:
                user_prompt += f"\nYOU ALREADY REQUESTED INFORMATION ABOUT {ai_provided_name} from tool `{ai_choice}`."
        else:
            print(f"Invalid choice: {ai_choice}")
            user_prompt += f"\nINVALID CHOICE: {ai_choice}"
            continue

        print(i, "NEW USER PROMPT:\n", user_prompt)
