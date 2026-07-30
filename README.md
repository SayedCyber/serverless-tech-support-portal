# Serverless Tech Support Portal
# Sayed Amini 
# Washington University - Cloud Computing

## Project Overview
This repository contains the capstone project for the Introduction to Cloud Computing course (Washington University in St. Louis, MACS Program, Summer 2026). The project implements a fully functional, event-driven **Serverless Tech Support Portal** designed to allow users to submit and track support tickets seamlessly without provisioning or managing underlying servers.

---
## Architecture

                    ┌─────────────────────────────┐
   User   ────────▶ │   S3 Static Site (frontend)  │
                    └──────────────┬───────────────┘
                                   │ HTTPS
                                   ▼
                    ┌──────────────────────────────┐
                    │       Amazon API Gateway     │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │       AWS Lambda (Python)    │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │      Amazon DynamoDB Table   │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │       SQS Queue & SNS        │
                    └──────────────────────────────┘
##  System Design
The application is built entirely on native AWS serverless components managed through **AWS CDK (Python)**. 

* **Frontend:** Hosted on **Amazon S3** as a static website.
* **API Gateway:** Acts as the secure HTTP entry point, managing CORS headers and routing incoming requests.
* **Compute:** **AWS Lambda** (Python 3.11 runtime) processes ticket creation and queries. It scales automatically to zero and handles variable traffic without idle server costs.
* **Database:** **Amazon DynamoDB** stores ticket records using a fast key-value schema (`ticket_id` partition key) configured with on-demand billing (`PAY_PER_REQUEST`).
* **Asynchronous Messaging:** **Amazon SQS** queues background tasks, and **Amazon SNS** handles alert notifications for new support requests.

---

## Key Architecture Decisions (ADR Summary)

| Component | Choice | Alternative Considered & Rejected | Justification |
| :--- | :--- | :--- | :--- |
| **Compute** | AWS Lambda | ECS Fargate | Lambda scales automatically to zero, eliminating fixed overhead and idle costs for intermittent ticket workloads. |
| **Database** | Amazon DynamoDB | RDS PostgreSQL | Tickets follow simple key-value patterns. DynamoDB provides instant serverless NoSQL scaling with zero schema migration overhead. |
| **IaC** | AWS CDK (Python) | Terraform | Aligns fully with the course codebase language, utilizing higher-level constructs to define infrastructure directly. |
| **Auth / SaaS** | *Deferred (MVP)* | Cognito / Stripe | Excluded from the 1-week MVP scope to focus cleanly on serverless event-driven architecture and eliminate PCI-DSS security risks. |

---

## Cost Estimate
Based on the AWS Pricing Calculator, assuming low-to-moderate ticket volume within the AWS Free Tier limits:

* **Amazon API Gateway:** $0.00 (Within 1M free requests/mo tier)
* **AWS Lambda:** $0.00 (Within 1M free requests tier)
* **Amazon DynamoDB:** $0.00 (Within 25 GB storage tier)
* **Amazon SQS & SNS:** $0.40
* **Amazon S3:** $0.00
* **Total Estimated Monthly Cost:** **~$4.80 / month** (Fully covered under AWS Free Tier)

---

## Repository Structure
```text
serverless-tech-support-portal/
│
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD automated deployment pipeline
├── app.py                      # CDK App entry point
├── cdk.json                    # CDK toolkit configuration
├── requirements.txt            # Python dependencies
├── serverless_tech_support_portal/
│   └── serverless_tech_support_portal_stack.py  # Main infrastructure stack
└── frontend/
    └── index.html              # Static web interface for ticket submission

## Setup & Deployment Instructions

### Prerequisites
* Python 3.11+ installed locally.
* Node.js and AWS CDK CLI installed globally (`npm install -g aws-cdk`).
* Active AWS account credentials configured via `aws configure`.

## Automated Deployment (CI/CD)
This repository uses GitHub Actions for automated deployments. Any code pushed to the main branch automatically triggers the pipeline, authenticates with AWS via Secrets, and executes cdk deploy

### Step-by-Step Deployment
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/sayedcyber/serverless-tech-support-portal.git
   cd serverless-tech-support-portal
   ```

2. **Activate the Python Virtual Environment:**
   * On Windows (PowerShell):
     ```bash
     .venv\Scripts\Activate
     ```
 

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Synthesize and Deploy the Stack:**
   ```bash
   cdk deploy
   ```

5. **Access the Application:**
   * Once deployment completes successfully, copy the `SiteURL` output from the terminal and open it in your browser to start submitting support tickets.

## Cost
Extremely cost-effective, operating almost entirely within the AWS Free Tier since it utilizes serverless technologies like Lambda, S3, API Gateway, and DynamoDB on-demand


## Future Improvements
Integrate Amazon Cognito for real user authentication and secure identity management.

Add Stripe payment gateway support for paid support requests.



---

## Author
* **Sayed Amini**  
* Washington University in St. Louis — MACS Program (Summer 2026)
