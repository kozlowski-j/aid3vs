import os
import base64
from openai import OpenAI
import logging
import time
import requests
from dotenv import load_dotenv

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


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('factory_analysis.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('factory_analyzer')


def image_to_base64(image_path, logger):
    logger.info(f'Converting image to base64: {image_path}')
    try:
        with open(image_path, 'rb') as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            logger.debug(f'Successfully encoded image: {image_path}')
            return encoded
    except Exception as e:
        logger.error(f'Error encoding image {image_path}: {str(e)}')
        raise


def extract_text_from_image(client, base64_image, logger):
    logger.info('Extracting text from image')
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract and return only the text visible in this image. If there's no text, respond with 'No text found'."
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
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f'Error extracting text from image: {str(e)}')
        raise


def analyze_content(client, content, content_type, logger):
    logger.info(f'Starting content analysis of type: {content_type}')
    start_time = time.time()
    system_prompt = """
        You are an expert in analyzing content.
        You will be given reports from a factory.
        Please categorize the reports containing information about captured people or traces of their PRESENCE,
        as well as notes about repaired hardware issues. Information about absence of people should be categorized as 'other'.
        Those related to software should be categorized as 'other'.
        Your task is to categorize reports into one of the following categories:
        - people
        - hardware
        - other
        Respond ONLY with the category name.
    """
    
    try:
        if content_type == 'text':
            logger.debug('Sending text to GPT-4')
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            )
            result = response.choices[0].message.content

        elif content_type == 'image':
            logger.debug('Extracting text from image before analysis')
            extracted_text = extract_text_from_image(client, content, logger)
            logger.debug(f'Extracted text: {extracted_text}')
            
            if extracted_text.lower() == 'no text found':
                logger.debug('No text found, analyzing image directly')
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": system_prompt,
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{content}"
                                    },
                                },
                            ],
                        }
                    ],
                )
                result = response.choices[0].message.content
            else:
                logger.debug('Analyzing extracted text')
                result = analyze_content(client, extracted_text, 'text', logger)

        elif content_type == 'audio':
            logger.debug('Starting audio transcription')
            with open('temp_audio.mp3', 'wb') as f:
                f.write(content)
            
            with open('temp_audio.mp3', 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            os.remove('temp_audio.mp3')
            logger.debug('Analyzing audio transcript')
            result = analyze_content(client, transcript.text, 'text', logger)

        elapsed_time = time.time() - start_time
        logger.info(f'Completed {content_type} analysis. Time: {elapsed_time:.2f}s. Result: {result}')
        return result

    except Exception as e:
        logger.error(f'Error during {content_type} analysis: {str(e)}')
        raise


def read_and_analyze_factory_files(openai_client, directory):
    logger = setup_logging()
    logger.info('Starting factory files analysis')
    
    # Initialize categorized results
    results = {
        "people": [],
        "hardware": []
    }
    
    try:
        files = [f for f in os.listdir(directory) if f.endswith(('.txt', '.png', '.mp3'))]
        logger.info(f'Found {len(files)} files to analyze')
        
        for filename in files:
            logger.info(f'Processing file: {filename}')
            file_path = os.path.join(directory, filename)
            
            try:
                if filename.endswith('.txt'):
                    logger.debug(f'Reading text file: {filename}')
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        analysis = analyze_content(openai_client, content, 'text', logger)
                
                elif filename.endswith('.png'):
                    logger.debug(f'Reading image file: {filename}')
                    base64_image = image_to_base64(file_path, logger)
                    analysis = analyze_content(openai_client, base64_image, 'image', logger)
                
                elif filename.endswith('.mp3'):
                    logger.debug(f'Reading audio file: {filename}')
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        analysis = analyze_content(openai_client, content, 'audio', logger)
                
                # Categorize based on analysis
                if analysis.lower() == 'people':
                    results['people'].append(filename)
                elif analysis.lower() == 'hardware':
                    results['hardware'].append(filename)
                
                logger.info(f'Successfully analyzed file: {filename} - Result: {analysis}')
                
            except Exception as e:
                logger.error(f'Error processing file {filename}: {str(e)}')
    
    except Exception as e:
        logger.critical(f'Critical error during analysis: {str(e)}')
        raise
    
    logger.info('Completed analysis of all files')
    logger.info(f"Files about people: {len(results['people'])}")
    logger.info(f"Files about hardware: {len(results['hardware'])}")
    logger.info(f"results: {results}")
    
    return results

if __name__ == '__main__':
    results = read_and_analyze_factory_files(openai_client, 'data/pliki_z_fabryki')

    final_results = {
        "people": sorted(results["people"]),
        "hardware": sorted(results["hardware"])
    }

    logging.info("Final results: {}".format(final_results))

    payload = {
        "task": "kategorie",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": final_results
    }
    logging.info(f"payload: {payload}")

    post_json_data_to_url(payload, f"{CENTRALA_BASE_URL}/report")
