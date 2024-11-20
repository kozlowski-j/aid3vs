import os

from dotenv import load_dotenv
from openai import OpenAI

from utils import post_json_data_to_url, read_txt_files

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


reports = read_txt_files("assignments/data/pliki_z_fabryki")
facts = read_txt_files("assignments/data/pliki_z_fabryki/facts")


def extract_person_name(text_content: str) -> str:
    response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Extract full name of the person this fact is about. "
                               "Return just the name, nothing else. If no person name is found, "
                               "return 'NO_NAME_FOUND'"
                },
                {
                    "role": "user",
                    "content": text_content
                }
            ]
        )
    return response.choices[0].message.content.strip()


updated_facts = {}

for fact_id, fact_content in facts.items():
    if fact_content.strip() == "entry deleted":
        updated_facts[fact_id] = fact_content
        continue
        
    person_name = extract_person_name(fact_content)
    
    if person_name == "NO_NAME_FOUND":
        updated_facts[fact_id] = fact_content
    else:
        updated_facts[person_name] = fact_content

print('updated_facts: ', updated_facts.keys())

system_prompt = """
You are a helpful assistant that extracts information from texts about people.

You will be given a set of facts about people.
Your task is to extract key words from the given text. 
Include information about the persons job if possible.
Include information about the number of the sector when possible.

Output key words MUST be in Polish.
Output key words MUST be in denominator form.
Output key words MUST be separated by commas.

EXAMPLES:
- Output: "sportowiec, centrala, niebo"
- Output: "dom, samochód, robot"
"""

results = {}
for report_id, report_content in reports.items():
    person_name = extract_person_name(report_content)
    print(report_id, 'person_name: ', person_name)
    person_facts = updated_facts.get(person_name, "")

    report_and_facts = f"Report name: {report_id}\n\nReport: {report_content}\n\nFacts: {person_facts}"

    response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": report_and_facts
                }
            ]
        )

    results[report_id] = response.choices[0].message.content.strip()

print('results: ', results)

payload = {
    "task": "dokumenty",
    "apikey": AIDEVS_MY_APIKEY,
    "answer": results
}
print(f"payload: {payload}")
post_json_data_to_url(payload, f"{CENTRALA_BASE_URL}/report")

