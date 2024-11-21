import json

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


def get_response_from_url(url, input_json):
    response = requests.get(url, json=input_json)
    return response.json()


def query_structure(sql_query_text):
    return {
        "task": "database",
        "apikey": AIDEVS_MY_APIKEY,
        "query": sql_query_text
}

starting_queries = [
    "show tables",
    "select * from users limit 10",
    "select * from datacenters limit 10"
]

info_about_db = []

for query in starting_queries:
    db_response = get_response_from_url(f"{CENTRALA_BASE_URL}/apidb", query_structure(query))

    info_about_db.append({"query": query, "database_response": db_response})

system_prompt = """
You are an expert SQL database analyst.
You are given a list of queries and responses from a MySQL database.
Your task is to analyze the response and provide a SQL query that answers the following question:
QUESTION: 
Which active data centers (DC_ID) are managed by employees who are on leave (is_active=0)?

You should use the provided queries and responses to craft a new query that will return the correct answer.
The query should return a UNIQUE list of DC_IDs.

You MUST return ONLY the SQL query that answers the question.
DO NOT use markdown formatting.
"""

response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": json.dumps(info_about_db)
            }
        ]
    )
new_query = response.choices[0].message.content

new_query = new_query.replace("```", "").replace("sql", "").strip()
print(new_query)

db_response = get_response_from_url(f"{CENTRALA_BASE_URL}/apidb", query_structure(new_query))

result = [item['dc_id'] for item in db_response['reply']]

payload = {
    "task": "database",
    "apikey": AIDEVS_MY_APIKEY,
    "answer": result
}
print(f"payload: {payload}")
post_json_data_to_url(payload, f"{CENTRALA_BASE_URL}/report")
