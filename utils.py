import requests
import json
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
