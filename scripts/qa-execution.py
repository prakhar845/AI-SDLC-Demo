name: Automated QA Execution Gate

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  qa_testing:
    runs-on: ubuntu-latest
    environment:
      name: QA-Approval-Gate # This pauses the workflow for the QA Engineer

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Dependencies
        run: npm ci

      # This runs the tests and saves the output to a text file
      - name: Execute QA Test Suite
        run: npm run test > qa_execution_log.txt
        continue-on-error: true # Ensures the log is saved even if a test fails

      # This uploads the text file so the QA Engineer can download it
      - name: Upload QA Artifact
        uses: actions/upload-artifact@v4
        with:
          name: QA-Test-Execution-Logs
          path: qa_execution_log.txt

      - name: Notify PR of Artifact
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `🧪 **QA Execution Complete!**\n\nThe automated test suite has finished running in the sandbox.\n\n📥 **Download the \`QA-Test-Execution-Logs\` artifact from the Actions tab above to review the results before approving.**`
            })
