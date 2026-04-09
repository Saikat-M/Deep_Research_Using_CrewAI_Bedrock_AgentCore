# Deep Research Using CrewAI & Bedrock AgentCore

Conduct structured, multi-step deep research and generate high-quality reports using a CrewAI multi-agent pipeline deployed on AWS Bedrock AgentCore.

---

## Architecture Overview

```
Streamlit UI → API Gateway → Lambda → Bedrock AgentCore → CrewAI Crew
                                  ↕
                              DynamoDB (session state)
```

The crew runs 4 agents sequentially:
1. **Research Planner** – breaks the query into a structured research plan
2. **Researcher** – gathers data using Exa search + web scraping
3. **Fact Checker** – verifies accuracy and flags misinformation
4. **Report Writer** – produces a final markdown report

---

## Prerequisites

- Python 3.10–3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd Deep_Research_Using_CrewAI_Bedrock_AgentCore
```

### 2. Create and activate a virtual environment

Using `uv` (recommended):
```bash
uv venv
```

Or using Python's built-in venv:
```bash
python -m venv .venv
```

Activate the virtual environment:

- **macOS/Linux:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows:**
  ```bash
  .venv\Scripts\activate
  ```

### 3. Install dependencies

Install all project dependencies (required for both running the Streamlit frontend locally and building the Docker image):

Using `uv sync` (recommended — installs exact versions from uv.lock):
```bash
uv sync
```

Or using `pip` with `requirements.txt`:
```bash
pip install -r requirements.txt
```

Then install `requests`, which is required by the Streamlit frontend but is not part of `requirements.txt` or `pyproject.toml`:
```bash
pip install requests
```

### 4. Configure the API URL

Update `API_URL` in `streamlit.py` with your deployed API Gateway URL:

```python
API_URL = "https://<api-id>.execute-<api.region>.amazonaws.com/<stsge-name>/<api-name>"
```

### 5. Run the app

```bash
streamlit run streamlit.py
```

---

## AWS CLI Setup

Installing and configuring the AWS CLI with your profile is required to build and push the Docker image using the Dockerfile in this repo to the AWS account where Bedrock AgentCore will host the Agentic application.

- **Install/Update AWS CLI** → [Getting Started with AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

- **Configure AWS CLI** with your IAM user credentials → [Authenticating using IAM user credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-authentication-user.html)

---

## Project Structure

```
├── src/deep_research/
│   ├── crew.py              # CrewAI crew + Bedrock AgentCore entrypoint
│   ├── main.py              # Local run / train / test entry points
│   ├── config/
│   │   ├── agents.yaml      # Agent role definitions
│   │   └── tasks.yaml       # Task definitions
│   └── tools/
│       └── custom_tool.py   # Template for adding custom tools
├── knowledge/
│   └── user_preference.txt  # User context injected into the crew
├── streamlit.py             # Streamlit frontend
├── lambda_function.py       # Lambda handler (async polling pattern)
├── Dockerfile               # Container image for AgentCore
├── requirements.txt         # Python dependencies
└── pyproject.toml           # Project metadata & script entry points
```
