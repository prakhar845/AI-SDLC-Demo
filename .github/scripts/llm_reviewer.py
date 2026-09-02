import os
import requests
import json

# Environment Variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') # Update your repository secret name to match this
PR_NUMBER = os.getenv('PR_NUMBER')
REPO_NAME = os.getenv('REPO_NAME')

# API Endpoints
GH_API_URL = f"https://api.github.com/repos/{REPO_NAME}/pulls/{PR_NUMBER}"
# Direct Google Gemini REST API endpoint
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"

headers_gh = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3.diff" # Requests the raw code diff
}

def get_pr_diff():
    """Fetches the code changes from the PR."""
    response = requests.get(GH_API_URL, headers=headers_gh)
    response.raise_for_status()
    return response.text

def generate_llm_report(diff):
    """Sends the diff to the Gemini API and enforces the rigid SDLC template."""
    
    system_instruction = """
    You are an expert Senior Software Engineer conducting a strict code review. 
    Analyze the provided Pull Request diff and generate a markdown report using EXACTLY this format:
    
    ### 🔍 Requirement Alignment
    [Evaluate if the code meets standard functional requirements]
    
    ### 🧱 Scalability Limits
    | Component | Potential Bottleneck | Recommended Fix |
    |-----------|----------------------|-----------------|
    | ... | ... | ... |
    
    ### ⚠️ Exception Handling & Breaking Scenarios
    | Scenario | Handled Properly? | Notes |
    |----------|-------------------|-------|
    | ... | ... | ... |
    """

    user_prompt = f"Review this PR Diff:\n\n{diff}"

    # Structured payload matching Google's Content schema hierarchy
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_instruction}
            ]
        },
        "generationConfig": {
            "temperature": 0.2, # Low temperature keeps output structured and strict
            "maxOutputTokens": 2048
        }
    }
    
    headers_gemini = {
        "Content-Type": "application/json"
    }

    response = requests.post(GEMINI_URL, headers=headers_gemini, json=payload)
    response.raise_for_status()
    
    # Navigate Gemini's specific JSON response structure
    response_json = response.json()
    try:
        return response_json['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexField):
        raise ValueError(f"Unexpected response format from Gemini API: {json.dumps(response_json)}")

def post_pr_comment(comment_body):
    """Posts the Gemini report as a comment on the PR."""
    url = f"https://api.github.com/repos/{REPO_NAME}/issues/{PR_NUMBER}/comments"
    payload = {"body": comment_body}
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

if __name__ == "__main__":
    print("Fetching PR Diff...")
    diff = get_pr_diff()
    
    # Safety truncation for large pull requests
    if len(diff) > 40000:
        diff = diff[:40000] + "\n\n...[DIFF TRUNCATED FOR LENGTH]"
        
    print("Generating Gemini Report...")
    report = generate_llm_report(diff)
    
    print("Posting to GitHub...")
    post_pr_comment(report)
    print("Success! Gemini Developer Gate report generated.")
