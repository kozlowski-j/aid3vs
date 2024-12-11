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

questions_url = f"https://centrala.ag3nts.org/data/{AIDEVS_MY_APIKEY}/gps_question.json"

# Get data from URL
response = requests.get(questions_url)
question = response.json()['question']
print(question)

openai_client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)

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

# Tools
def get_people_from_api(person_name: str):
    """
    Returns a list of places visited by a person.

    Args:
        person_name (str): The name of the person.

    Returns:
        list: A list of places visited by the person.

    Example: ["WARSZAWA", "KRAKOW", "LUBLIN"]
    """
    print("Getting places for:", person_name)
    person_name = clean_name(person_name)
    people_url = f"{CENTRALA_BASE_URL}/people"
    people_response = requests.get(people_url, json={
        "query": person_name,
        "apikey": AIDEVS_MY_APIKEY
    })
    places = people_response.json()['message'].split(' ')
    print("places:", places)
    return places

def get_places_from_api(place_name: str):
    """
    Returns a list of people spotted in a place.

    Args:
        place_name (str): The name of the place.

    Returns:
        list: A list of people spotted in the place.

    Example: ["RAFAL", "AZAZEL", "MARIA"]
    """
    print("Getting people for:", place_name)
    place_name = clean_name(place_name)
    places_url = f"{CENTRALA_BASE_URL}/places"
    places_response = requests.get(places_url, json={
        "query": place_name,
        "apikey": AIDEVS_MY_APIKEY
    })
    people = places_response.json()['message'].split(' ')
    print("people:", people)
    return people

def get_persons_location_from_gps_api(user_id: int):
    """
    Returns the location of a person.

    Args:
        user_id (int): The ID of the user.

    Returns:
        dict: The location of the user.

    Example: {"lat": 52.2297, "long": 21.0122}
    """
    print("Getting GPS for user_id:", user_id)
    gps_url = f"{CENTRALA_BASE_URL}/gps"
    headers = {'Content-Type': 'application/json'}
    gps_response = requests.get(
        gps_url,
        json={
            "userID": user_id
        },
        headers=headers
    )
    gps = gps_response.json()["message"]
    print("gps:", gps)
    return gps

def get_persons_user_id(person_name: str):
    """
    Get the user ID of a person from the users database.
    Args:
        person_name (str): The name of the person.

    Returns:
        int: ID of the person
    """
    person_name = clean_name(person_name)
    person_name = person_name.title()
    print("Getting user ID for", person_name)

    sql_query_text = f"SELECT id FROM users WHERE username = '{person_name}'"
    users_url = f"{CENTRALA_BASE_URL}/apidb"
    users_response = requests.get(users_url, json={
        "task": "database",
        "apikey": AIDEVS_MY_APIKEY,
        "query": sql_query_text
    })
    user_id = users_response.json()['reply'][0]['id']
    print("user_id:", user_id)
    return user_id

# Tools definition for OpenAI function calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_people_from_api",
            "description": "Returns a list of places visited by a person",
            "parameters": {
                "type": "object",
                "properties": {
                    "person_name": {
                        "type": "string",
                        "description": "The name of the person"
                    }
                },
                "required": ["person_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_places_from_api",
            "description": "Returns a list of people spotted in a place",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "The name of the place"
                    }
                },
                "required": ["place_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_persons_location_from_gps_api",
            "description": "Returns the GPS location of a person",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The ID of the user"
                    }
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_persons_user_id",
            "description": "Get the user ID of a person",
            "parameters": {
                "type": "object",
                "properties": {
                    "person_name": {
                        "type": "string",
                        "description": "The name of the person"
                    }
                },
                "required": ["person_name"]
            }
        }
    }
]

def answer_question(question: str):
    system_prompt = """
    You are a helpful assistant with access to various location-tracking tools. 
    Your task is to answer questions about people's locations and movements accurately and concisely.
    Use the provided tools to:
    - Check where people have been
    - Find who was in specific places
    - Get current GPS coordinates
    - Look up user IDs
    Always provide direct, factual answers based on the tool results.
    Do not make assumptions or include unnecessary information.
    In case of ambiguity or conflicting indicators, provide detailed reasoning in the "_thinking" field to justify your choice.

    <output_format>
    Always respond with this JSON structure.
    {
        "imie": {
            "lat": 12.345,
            "lon": 65.431
        },
        "kolejne-imie": {
            "lat": 19.433,
            "lon": 12.123
        }
    }
    Do not use the markdown json formatting.
    </output_format>
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    print(response_message)
    
    # Continue conversation while there are tool calls
    while response_message.tool_calls:
        tool_calls = response_message.tool_calls
        messages.append(response_message)
        
        # Execute each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Dynamically calls a function by its name from global namespace
            # For example, if function_name is "get_location", it will call get_location()
            # The **function_args unpacks the JSON arguments into keyword arguments
            function_response = globals()[function_name](**function_args)
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(function_response)
            })
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        response_message = response.choices[0].message
    
    return response_message.content

# Use the function to answer the question
answer = answer_question(question)
print(f"Answer: {answer}")

answers_as_json = json.loads(answer.replace("```json", "").replace("```", ""))

final_payload = {
    "task": "gps",
    "apikey": AIDEVS_MY_APIKEY,
    "answer": answers_as_json
}
final_response = post_json_data_to_url(final_payload, f"{CENTRALA_BASE_URL}/report")