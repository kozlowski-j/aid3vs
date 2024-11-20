import requests
import json
import os


def post_json_data_to_url(payload: dict, submit_url: str):
    # Submit the processed output
    headers = {'Content-Type': 'application/json'}
    submission_response = requests.post(submit_url, json=payload, headers=headers)

    if submission_response.status_code == 200:
        print("Submission successful.")
        print(submission_response.json())
        print(submission_response.text)
    else:
        print(f" Submission failed. Status code: {submission_response.status_code}")
        print(submission_response.text)
        print(submission_response.json())


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


def read_txt_files(data_path: str) -> dict:
    files_dict = {}
    
    for filename in os.listdir(data_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(data_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                files_dict[filename] = f.read()
                
    return files_dict
