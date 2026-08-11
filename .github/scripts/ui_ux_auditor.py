import os
import base64
import requests
import json
from playwright.sync_api import sync_playwright

# Environment Setup
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PR_NUMBER = os.getenv('PR_NUMBER')
REPO_NAME = os.getenv('REPO_NAME')
PREVIEW_URL = os.getenv('PREVIEW_URL')

# Production Endpoint for Gemini 3 Series
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

def take_screenshot(url, output_path="preview.png"):
    """Launches Playwright headless browser to capture the preview page."""
    print(f"Navigating headless browser to: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Set viewport to standard desktop layout
        page.set_viewport_size({"width": 1280, "height": 800})
        # Wait until network requests are fully idle to ensure content loads
        page.goto(url, wait_until="networkidle")
        page.screenshot(path=output_path, full_page=True)
        browser.close()
    print("Screenshot captured successfully.")
    return output_path

def analyze_ui_vision(image_path):
    """Sends the base64 screenshot to Gemini 2.5 Flash for visual layout compliance validation."""
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    system_instruction = """
    You are an expert Frontend QA Engineer and UI/UX Auditor.
    Analyze the provided screenshot of the live web deployment. Review its structure, component spacing, text legibility, and visual elements.
    
    Generate an alignment report using EXACTLY this markdown template:
    
    ### 🎨 UI/UX Component Alignment Audit
    [Provide a macro analysis of the interface layout structure, responsiveness, and item hierarchy]
    
    ### 📐 Design System & Layout Discrepancies
    | Target UI Component | Detected Layout Issue | Severity (Low/Med/High) | Suggested Correction |
    |--------------------|----------------------|-------------------------|----------------------|
    | ... | ... | ... | ... |
    
    ### ♿ Contrast & Accessibility Observances
    [Note any immediate visibility issues, text size conflicts, or overlapping content layouts]
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": img_base64
                        }
                    },
                    {
                        "text": "Audit this interface screenshot against professional clean UI layout standards."
                    }
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_instruction}
            ]
        },
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048
        }
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(GEMINI_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()['candidates'][0]['content']['parts'][0]['text']

def post_pr_comment(comment_body):
    """Posts the completed UI/UX report as a comment on the PR thread."""
    url = f"https://api.github.com/repos/{REPO_NAME}/issues/{PR_NUMBER}/comments"
    payload = {"body": comment_body}
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

if __name__ == "__main__":
    # Fallback to homepage url if no preview url is passed dynamically
    target_url = PREVIEW_URL if PREVIEW_URL else f"https://{REPO_NAME.split('/')[0]}.github.io/{REPO_NAME.split('/')[1]}/"
    
    try:
        screenshot_file = take_screenshot(target_url)
        print("Sending screen capture to Gemini 2.5 Flash...")
        ui_report = analyze_ui_vision(screenshot_file)
        print("Posting UI/UX validation to Pull Request...")
        post_pr_comment(ui_report)
        print("Success! Phase 3 Vision Audit Posted.")
    except Exception as e:
        print(f"Pipeline Interrupted: {str(e)}")
        # Gracefully handle preview failures without blocking development
        post_pr_comment(f"⚠️ **UI/UX Vision Runner Alert:** Automated vision screenshot failed to process check.\nReason: `{str(e)}`")
