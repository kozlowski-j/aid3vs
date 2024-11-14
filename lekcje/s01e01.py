import requests

from utils import get_url_text, get_custom_response, post_params_to_url
import webbrowser

xyz_url = 'https://xyz.ag3nts.org'

system_message = """
You are an expert Web Software Developer. 
You will be given a full code of an HTML website. Your task is to find a human-question provided in code and answer it.
<Examples>
Question:<br />Rok założenia Facebooka?
AI: 2004

Question:<br />Kiedy wybuchła Druga Wojna Światowa?
AI: 1939

Question:<br />Rok zabójstwa Johna F. Kennedy'ego?
AI: 1963
</Examples>
"""

site_html = get_url_text(xyz_url)

ai_response = get_custom_response(site_html, system_message)
print(ai_response)

params = f"username=tester&password=574e112a&answer={int(ai_response)}"
data = {
    "username": "tester",
    "password": "574e112a",
    "answer": int(ai_response)
}
print(params)

post_response = requests.post(xyz_url, data=data)

webbrowser.open(post_response.url)