import os
import sys
import json
import requests
import base64
from playwright.sync_api import sync_playwright

def capture_screenshot(html_file_path, output_image_path):
    if not os.path.exists(html_file_path):
        print(f"Error: {html_file_path} not found in the repository.")
        sys.exit(1)
        
    # Convert local file path to a browser-readable URI
    file_uri = f"file://{os.path.abspath(html_file_path)}"
    
    # Spin up a headless Chromium browser and take a picture
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(file_uri)
        page.screenshot(path=output_image_path, full_page=True)
        browser.close()

def audit_with_gemini(image_path, api_key):
    # Encode the image so it can be sent through the API JSON payload
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # Send the strict prompt alongside the encoded screenshot
    payload = {
        "contents": [{
            "parts": [
                {"text": "Act as an Expert UI/UX Designer. Audit this web page screenshot. Evaluate the layout, typography, visual hierarchy, and overall user experience. Provide a markdown-formatted critique with a 'UI/UX Score' out of 10 and bullet points for 'Areas of Improvement'."},
                {"inline_data": {"mime_type": "image/png", "data": encoded_image}}
            ]
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        print(f"Gemini API Error: {response.text}")
        sys.exit(1)

def post_github_comment(repo, pr_number, token, comment_body):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"body": comment_body}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    API_KEY = os.environ.get("GEMINI_API_KEY")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
    
    # Dynamically extract the PR number from GitHub's internal environment event map
    try:
        with open(os.environ.get("GITHUB_EVENT_PATH"), 'r') as f:
            PR_NUMBER = json.load(f)['pull_request']['number']
    except:
        print("Could not determine PR number. Exiting.")
        sys.exit(1)

    screenshot_path = "preview.png"
    print("Capturing screenshot of index.html...")
    capture_screenshot("index.html", screenshot_path)
    
    print("Sending screenshot to Gemini for Visual Audit...")
    audit_text = audit_with_gemini(screenshot_path, API_KEY)
    
    print("Posting visual critique to GitHub...")
    post_github_comment(GITHUB_REPOSITORY, PR_NUMBER, GITHUB_TOKEN, f"## 🎨 Phase 3: AI UI/UX Visual Audit\n\n{audit_text}")
