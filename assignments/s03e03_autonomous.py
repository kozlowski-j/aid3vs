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


prompt = """
Act as an expert MySQL database analyst.

Your OBJECTIVE is to analyze the database structure and provide a SQL query that answers the following QUESTION:
QUESTION:
Which active data centers (DC_ID) are managed by employees who are on leave (is_active=0)?

Instructions:
•	You may use queries and their results to understand the database structure and craft subsequent queries to help you return the correct answer.
•	The final query should return a UNIQUE list of DC_IDs.
•	Do not use markdown formatting.
•	Your response must be only a single MySQL query.
•	Pay attention to table names and column names.
•	Remember that you are working with a MySQL database.
•	When you have the query that answers the OBJECTIVE, return 'OBJECTIVE_QUERY' followed by the SQL query.
•	Start with the 'SHOW TABLES' query.
•	Remember to answer only with MySQL query.
- DO NOT output QUERY_N

Example Answer:

SELECT * FROM table_name WHERE column_name = 'value' ;
"""

new_query = ""
db_response = ""
i = 0

while (i < 10) and ("OBJECTIVE_QUERY" not in new_query):
    print(f"Iteration {i}")
    if i == 1:
        prompt += "#### Previous queries for reference:"

    print(prompt)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    new_query = response.choices[0].message.content

    new_query = new_query.replace("```", "").replace("sql", "").replace("\n", "").strip()
    print("Chat response:", new_query)

    db_response = get_response_from_url(f"{CENTRALA_BASE_URL}/apidb", query_structure(new_query))
    print(db_response)
    prompt += f"\n{new_query}\n{db_response}"
    i += 1

print("Left loop.")
final_query = (new_query
               .replace("```", "")
               .replace("sql", "")
               .replace("OBJECTIVE_QUERY", "")
               .strip())

print("Final Query:", final_query)
db_response = get_response_from_url(f"{CENTRALA_BASE_URL}/apidb", query_structure(final_query))
result = [item['dc_id'] for item in db_response['reply']]

payload = {
    "task": "database",
    "apikey": AIDEVS_MY_APIKEY,
    "answer": result
}
print(f"payload: {payload}")
post_json_data_to_url(payload, f"{CENTRALA_BASE_URL}/report")
