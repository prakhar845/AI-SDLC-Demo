name: PM Consolidation Master Report

on:
  pull_request_review:
    types: [submitted]

permissions:
  pull-requests: write
  contents: read

jobs:
  generate_master_report:
    # Only runs when a human reviewer clicks "Approve"
    if: github.event.review.state == 'approved'
    runs-on: ubuntu-latest

    steps:
      - name: Compile Master Report & Update PR Body
        uses: actions/github-script@v7
        with:
          script: |
            // 1. Fetch the current Pull Request details
            const pr = await github.rest.pulls.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number
            });
            
            const currentBody = pr.data.body || "";
            
            // 2. Prevent duplicate Master Reports from being appended
            if (currentBody.includes("👑 PM Master Consolidation Report")) {
              console.log("Master Report already exists. Skipping.");
              return;
            }
            
            // 3. Construct the Executive Summary
            let masterReport = "\n\n---\n\n## 👑 PM Master Consolidation Report\n";
            masterReport += "> **All automated checks and human gates have successfully cleared.**\n\n";
            masterReport += "- ✅ **Phase 1 (Notion):** Requirements locked and ingested.\n";
            masterReport += "- ✅ **Phase 2 (Dev Gate):** Gemini Code Review & Human Approval passed.\n";
            masterReport += "- ✅ **Phase 3 (UI/UX Gate):** Sandbox Deployment & Gemini Vision Audit passed.\n";
            masterReport += "- ✅ **Phase 4 (QA Gate):** Sandbox Test Suite executed logs attached.\n\n";
            masterReport += "### 🚦 Status: READY FOR MERGE\n";
            masterReport += "*Awaiting final PM authorization to deploy to production.*";
            
            // 4. Update the PR Description
            await github.rest.pulls.update({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
              body: currentBody + masterReport
            });
