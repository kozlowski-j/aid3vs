import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
import re

from utils import post_json_data_to_url


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION_ID")
CENTRALA_BASE_URL = os.getenv("CENTRALA_BASE_URL")
AIDEVS_MY_APIKEY = os.getenv("AIDEVS_MY_APIKEY")

# Construct URL with API key
url = f"https://centrala.ag3nts.org/data/{AIDEVS_MY_APIKEY}/softo.json"

# Get data from URL
response = requests.get(url)
questions = response.json()
print(questions)

openai_client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)

def extract_markdown_from_page(url):
    """Extract markdown content from webpage"""
    response = requests.get(url)
    # Convert HTML to markdown
    markdown_content = markdownify(response.text, heading_style="ATX")
    return markdown_content.strip()

def get_gpt_response(system_prompt: str, prompt: str) -> dict:
    """Get response from GPT model and parse it to JSON"""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
        
    gpt_response = response.choices[0].message.content.strip()
    gpt_response = gpt_response.replace("```json", "").replace("```", "")
    print(f"gpt_response:\n{gpt_response}")
    return json.loads(gpt_response)

def analyze_with_gpt_for_answer(content, question):
    """Use GPT to analyze markdown content and find answer"""
    system_prompt = """
    You are a proffessional website analyzer.
    You are given a question and a website content.
    The question will be in Polish.

    <prompt_objective>
    Analyze website content to find a clear answer to the question.
    Provide thorough reasoning in the "_thinking" field.
    Always respond with a valid JSON object without markdown blocks.
    </prompt_objective>

    <prompt_rules>
    - **Decision-making process:**
        1. Carefully analyze the website content for clarity and quality.
        2. Evaluate if the content clearly answers the question.
        3. If adjustments are required, select the most suitable command with as few mistakes as possible.
    - **Decision-making guidelines:**
        - If the content does not answer the question, return 'NO_ANSWER'.
        - If the content answers the question, return the answer.
    - Be concise and exact.
    - Always prioritize accuracy when deciding the answer to minimize errors.
    - In case of ambiguity or conflicting indicators, provide detailed reasoning in the "_thinking" field to justify your choice.
    - Always respond with a valid JSON object without markdown blocks.
    </prompt_rules>

    <output_format>
    Always respond with this JSON structure:
    {
        "_thinking": "Detailed explanation of your interpretation process, consideration of options, reasoning for decisions, and any assumptions made.",
        "answer": "answer to the question or NO_ANSWER"
    }
    </output_format>
    """

    prompt = f"""
    <question>
    {question}
    </question>
    <website_content>
    {content}
    </website_content>
    """

    gpt_response_json = get_gpt_response(system_prompt, prompt)
    return gpt_response_json["answer"]

def analyze_with_gpt_for_next_step(content, question):
    """Use GPT to analyze markdown content and find next step"""
    system_prompt = """
    You are a proffessional website analyzer.
    You are given a question and a website content.\
    The question will be in Polish.

    <prompt_objective>
    Analyze websites content to decide which URL on the website to visit next to answer the question given in the prompt. 
    Provide thorough reasoning in the "_thinking" field.
    Always respond with a valid JSON object without markdown blocks.
    </prompt_objective>

    <prompt_rules>
    - **Decision-making process:**
        1. Carefully analyze the website content for clarity and quality.
        2. Evaluate which URL on the website to visit next to answer the question.
        3. You MUST always return a valid URL.
        4. Return the URL that is the most likely to contain the answer to the question.
    - Be concise and exact.
    - Always prioritize accuracy when deciding the next step to minimize errors.
    - In case of ambiguity or conflicting indicators, provide detailed reasoning in the "_thinking" field to justify your choice.
    - Always respond with a valid JSON object without markdown blocks.
    </prompt_rules>

    <output_format>
    Always respond with this JSON structure:
    {
        "_thinking": "Detailed explanation of your interpretation process, consideration of options, reasoning for decisions, and any assumptions made.",
        "next_step": "URL to visit next"
    }
    </output_format>
    """
    
    prompt = f"""
    <question>
    {question}
    </question>
    <website_content>
    {content}
    </website_content>
    """

    gpt_response_json = get_gpt_response(system_prompt, prompt)
    return gpt_response_json["next_step"]

def find_answer_on_page(url, question, visited=None):
    """Search for answer on given page and its subpages using GPT"""
    if visited is None:
        visited = set()
    
    if url in visited:
        return None
    
    visited.add(url)
    print(f"Checking URL: {url}")
    
    # Extract markdown content
    content = extract_markdown_from_page(url)
    if not content:
        return None
    
    # Try to find answer on current page
    answer = analyze_with_gpt_for_answer(content, question)
    if answer != "NO_ANSWER":
        return answer
    
    # If no answer found, ask GPT for next URL to check
    next_url = analyze_with_gpt_for_next_step(content, question)
    if next_url != "NO_NEXT_STEP" :
        if next_url.startswith('http') and 'softo.ag3nts.org' in next_url:
            return find_answer_on_page(next_url, question, visited)
        elif next_url.startswith('/'):
            return find_answer_on_page(base_url + next_url, question, visited)
        else:
            print(f"Invalid next URL: {next_url}")
            return None
    
    return None

# Process each question
answers = {}
base_url = "https://softo.ag3nts.org"

for question_number in questions.keys():
    question = questions[question_number]
    print(f"\nProcessing question: {question}")
    answer = find_answer_on_page(base_url, question)
    if answer:
        answers[question_number] = answer
        print(f"Found answer: {answer}")
    else:
        print(f"No answer found for: {question}")

print("\nAll answers:", answers)

final_payload = {
    "task": "softo",
    "apikey": AIDEVS_MY_APIKEY,
    "answer": answers
}
final_response = post_json_data_to_url(final_payload, f"{CENTRALA_BASE_URL}/report")