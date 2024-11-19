import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import hashlib
import mimetypes
from openai import OpenAI
import base64
import json
from markdownify import markdownify as md

from dotenv import load_dotenv

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


class DocumentToMarkdown:

    def __init__(self, base_url, output_dir="indexed_content"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.media_dir = os.path.join(output_dir, "media")
        self.markdown_content = []
        self.openai_client = openai_client
        self.create_directories()
        
    def create_directories(self):
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.media_dir, exist_ok=True)
    
    def download_media(self, url, media_type):
        response = requests.get(url)
        if response.status_code == 200:
            file_hash = hashlib.md5(url.encode()).hexdigest()
            ext = mimetypes.guess_extension(response.headers['content-type'])
            filename = f"{file_hash}{ext}"
            filepath = os.path.join(self.media_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath

    def transcribe_audio(self, audio_path):
        """Transcribes audio file using OpenAI API"""
        with open(audio_path, "rb") as audio_file:
            transcript = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text

    def get_image_description(self, image_path):
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe what you see in the image. Be precise and detailed. Response should have max. 5 sentences."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content

    def process_document(self):
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Process images before conversion
        for img in soup.find_all('img'):
            img_url = urljoin(self.base_url, img.get('src', ''))
            saved_path = self.download_media(img_url, 'image')
            if saved_path:
                image_description = self.get_image_description(saved_path)
                new_p = soup.new_tag('p')
                new_p.string = f"[Image description: {image_description}]"
                img.replace_with(new_p)
        
        # Process audio files
        for audio in soup.find_all('audio'):
            source = audio.find('source')
            if source:
                audio_url = urljoin(self.base_url, source.get('src', ''))
                saved_path = self.download_media(audio_url, 'audio')
                if saved_path:
                    transcription = self.transcribe_audio(saved_path)
                    if transcription:
                        # Create new p tag with transcription
                        new_p = soup.new_tag('p')
                        new_p.string = f"[Audio Transcription:\n {transcription}]"
                        # Replace audio tag with transcription paragraph
                        audio.replace_with(new_p)
        
        # Convert HTML to Markdown
        markdown_text = md(str(soup))
        self.markdown_content.append(markdown_text)
        
        self.save_markdown()

    
    def save_markdown(self):
        """Saves content to Markdown file"""
        output_path = os.path.join(self.output_dir, 'document.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(self.markdown_content))


class MarkdownAnalyzer:
    def __init__(self):
        self.client = openai_client
        self.questions_url = f"{CENTRALA_BASE_URL}/data/{AIDEVS_MY_APIKEY}/arxiv.txt"
    
    def fetch_questions(self):
        """Fetches and parses questions from URL into a dictionary."""
        try:
            response = requests.get(self.questions_url)
            response.raise_for_status()
            questions_text = response.text
            
            # Parse questions into dictionary format
            questions_dict = {}
            for line in questions_text.split('\n'):
                if line.strip():
                    question_id, question = line.split('=', 1)
                    questions_dict[question_id.strip()] = question.strip()
            return questions_dict
        except requests.RequestException as e:
            raise Exception(f"Error while fetching questions: {e}")
    
    def translate_markdown(self, markdown_content: str) -> str:
        """Translates markdown content from Polish to English."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Translate the following markdown text from Polish to English. Preserve all markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": markdown_content
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Translation error: {e}")

    def analyze_markdown(self, markdown_content: str):
        """Analyzes markdown document and returns answers in specified format."""
        questions_dict = self.fetch_questions()
        print(questions_dict)
        answers = {}
        
        # Translate content before analysis
        translated_content = self.translate_markdown(markdown_content)
        
        try:
            for question_id, question in questions_dict.items():
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system", 
                            "content": "Provide a single-sentence answer to the question based on the markdown document provided. Be concise and direct."
                        },
                        {
                            "role": "user", 
                            "content": f"Document:\n{translated_content}\n\nQuestion:\n{question}"
                        }
                    ]
                )
                answer = response.choices[0].message.content.strip()
                print("Question:", question)
                print("Answer:", answer)
                answers[question_id] = answer
            
            return answers
            
        except Exception as e:
            raise Exception(f"Error during analysis: {e}")
    
    def save_results(self, results, output_file: str = "answers.json"):
        """Saves results to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # Convert HTML to Markdown
    # converter = DocumentToMarkdown(f'{CENTRALA_BASE_URL}/dane/arxiv-draft.html')
    # converter.process_document()
    
    # Read generated markdown file
    with open(os.path.join("indexed_content", 'document.md'), 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Analyze content
    analyzer = MarkdownAnalyzer()
    results = analyzer.analyze_markdown(markdown_content)
    analyzer.save_results(results)

    print(results)

    payload = {
        "task": "arxiv",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": results
    }
    print(f"payload: {payload}")

    # Submit the processed output
    submit_url = f"{CENTRALA_BASE_URL}/report"
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