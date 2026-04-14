# Career Compass 🧭

> AI-powered job application tracker for professionals in career transition.

Built with Python + Claude AI + Gmail API — automatically tracks your job applications by reading your inbox and classifying emails in real time.

---

## Features

- **Automated email tracking** — connects to Gmail and detects job-related emails
- **AI classification** — uses Claude AI to identify application confirmations, interview invitations, offers, and rejections
- **Smart filtering** — excludes newsletters and marketing, focuses on real recruiter emails
- **CLI interface** — simple terminal app to manage your applications
- **Local & private** — all data stays on your machine

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| AI | Claude AI (Anthropic API) |
| Email | Gmail API (Google OAuth 2.0) |
| Storage | JSON (local) |
| Testing | pytest |

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/larissa-borges89/career-compass.git
cd career-compass
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and add your API keys:
```
ANTHROPIC_API_KEY=your_key_here
```

### 5. Set up Gmail API
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create a project and enable the Gmail API
- Download OAuth credentials as `credentials.json` to the project root

### 6. Run the app
```bash
python main.py
```

---

## Usage

```
=== Career Compass ===
1. Add application
2. List applications
3. Update status
4. Sync emails to tracker
5. Exit
```

Option **4** connects to Gmail, classifies all job-related emails using Claude AI, and automatically updates your tracker.

---

## Project Structure

```
career-compass/
├── src/
│   ├── tracker.py      # Core application logic
│   ├── claude_ai.py    # Claude AI integration
│   └── gmail_api.py    # Gmail API integration
├── tests/
│   └── test_tracker.py # Unit tests
├── main.py             # CLI entry point
├── requirements.txt    # Dependencies
└── .env.example        # Environment variables template
```

---


## Job Search Pipeline

Career Compass automatically finds and scores job opportunities based on your resume:

### Job Sources

| Source | Coverage | Notes |
|--------|----------|-------|
| Adzuna API | LinkedIn, Indeed, Glassdoor + more | Direct API, immediate access |
| SerpAPI (Google Jobs) | All major job boards aggregated | 100 free searches/month |

Both sources cover jobs originally posted on LinkedIn and Indeed without requiring their restrictive API access.

### Ghost Job Detection

Jobs older than 48 hours are automatically filtered out — following recruiter best practices for maximizing response rates.

## Roadmap

- [x] Core tracker with CLI
- [x] Gmail API integration
- [x] Claude AI email classification
- [x] Automated email-to-tracker sync
- [x] Resume upload and parsing
- [x] Job search with AI matching (Adzuna + Google Jobs)
- [ ] REST API with FastAPI
- [ ] Web interface with React

---

## Author

**Larissa Borges** — Senior Software Engineer  
[GitHub](https://github.com/larissa-borges89)

---

*Open source tool for professionals navigating career transitions.*
