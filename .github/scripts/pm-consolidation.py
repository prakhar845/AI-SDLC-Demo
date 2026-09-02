import os
import sys
import json
import time
import requests

def post_comment(repo, pr_num, token, body):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_num}/comments"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    requests.post(url, headers=headers, json={"body": body})

def get_check_runs(repo, sha, token):
    url = f"https://api.github.com/repos/{repo}/commits/{sha}/check-runs"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    return response.json().get('check_runs', [])

if __name__ == "__main__":
    TOKEN = os.environ.get("GITHUB_TOKEN")
    REPO = os.environ.get("GITHUB_REPOSITORY")
    
    # Extract the PR data from the runner environment
    with open(os.environ.get("GITHUB_EVENT_PATH"), 'r') as f:
        event = json.load(f)
        PR_NUMBER = event['pull_request']['number']
        SHA = event['pull_request']['head']['sha']

    print("Pausing for 60 seconds to allow AI Review, UI Audit, and QA gates to finish...")
    time.sleep(60)

    # Fetch the final status of all parallel workflows
    checks = get_check_runs(REPO, SHA, TOKEN)
    
    dashboard = "## 📊 Phase 5: PM Consolidation Dashboard\n\n"
    dashboard += "| SDLC Phase | Final Status | Conclusion |\n"
    dashboard += "|---|---|---|\n"
    
    all_success = True
    for check in checks:
        name = check.get('name', 'Unknown')
        status = check.get('status', 'Unknown')
        conclusion = check.get('conclusion', 'pending')
        
        # Filter out this exact script so it doesn't grade itself
        if "PM Consolidation" not in name:
            dashboard += f"| **{name}** | `{status}` | `{conclusion}` |\n"
            if conclusion != "success" and conclusion != "skipped":
                all_success = False
    
    if all_success:
        dashboard += "\n### 🚀 Executive Summary\n**All automated SDLC gates have passed.** The feature is completely verified by Gemini, visually audited, and functionally QA tested. It is approved for production merge."
    else:
        dashboard += "\n### ⚠️ Executive Summary\n**Pipeline anomalies detected.** One or more automated gates failed. Please review the specific Phase logs above before merging."

    print("Posting PM Dashboard to GitHub...")
    post_comment(REPO, PR_NUMBER, TOKEN, dashboard)
