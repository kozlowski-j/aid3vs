import requests
import json
from openai import OpenAI, OpenAIError
import os


def get_url_text(url: str) -> str:
    # Send the GET request
    response = requests.get(url)
    text_data = response.text
    # Check if the request was successful
    if response.status_code == 200:
        # Get the text data
        print('Request successful:', text_data[:100])
        return text_data
    else:
        print('Failed to retrieve data:', response.status_code, text_data[:100])
        return ""


def post_json_data_to_url(data: dict, url: str):
    # Send the POST request
    response = requests.post(url, data=json.dumps(data))

    # Check the response
    if response.status_code == 200:
        print('Response:', response)
        return response
    else:
        print('Failed to send request:', response.status_code, response.text)


def post_params_to_url(params: str, url: str):
    # Send the POST request
    response = requests.post(url, params=params)

    # Check the response
    if response.status_code == 200:
        print('Response:', response)
        return response
    else:
        print('Failed to send request:', response.status_code, response.text)


def get_custom_response(prompt: str, system_message: str) -> str:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    openai_client = OpenAI(
        organization='org-JeEFAHu6LLth5RQlRKTfJDwE',
        project='proj_lAY8moAOvRQmMDewFPPnW1Te',
        api_key=OPENAI_API_KEY,
    )

    try:
        chat_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            max_tokens=10000,  # Limit the response length
            temperature=0.7,  # Adjust creativity (0 = deterministic, 1 = creative)
        )
        return chat_response.choices[0].message.content
    except OpenAIError as e:
        print(f"An error occurred: {e}")
        return ""


def verify_json(json_str, required_keys=None):
    """
    Verifies if a string is a valid JSON object and optionally checks for required keys.

    Args:
        json_str (str): The JSON string to validate.
        required_keys (list, optional): List of keys that must be present in the JSON object.

    Returns:
        dict: The parsed JSON object if it is valid and contains required keys.

    Raises:
        ValueError: If the JSON is invalid or required keys are missing.
    """
    try:
        # Parse JSON string
        if isinstance(json_str, str):
            json_obj = json.loads(json_str)
        elif isinstance(json_str, dict):
            json_obj = json_str
        else:
            raise ValueError("Must be dict or str.")

        # Ensure the JSON is a dictionary
        if not isinstance(json_obj, dict):
            raise ValueError("JSON is valid but not an object (dict).")

        # Check for required keys, if specified
        if required_keys:
            missing_keys = [key for key in required_keys if key not in json_obj]
            if missing_keys:
                raise ValueError(f"JSON is missing required keys: {', '.join(missing_keys)}")

        return json_obj

    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format.")
