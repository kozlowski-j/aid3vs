import requests
import json

# data
data_url = 'https://poligon.aidevs.pl/dane.txt'

# Send the GET request
response = requests.get(data_url)

# Check if the request was successful
if response.status_code == 200:
    # Get the text data
    text_data = response.text
    print('Text data:', text_data)
else:
    text_data = []
    print('Failed to retrieve data:', response.status_code, response.text)

# Define the API endpoint
verify_url = 'https://poligon.aidevs.pl/verify'

# Define the JSON payload
payload = {
    "task": "POLIGON",
    "apikey": "340a21f9-ceb6-4b9c-8ac8-2358a8ca204a",
    "answer": text_data.split('\n')[:2]
}

# Send the POST request
response = requests.post(verify_url, data=json.dumps(payload))

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    response_data = response.json()
    print('Response:', response_data)
else:
    print('Failed to send request:', response.status_code, response.text)