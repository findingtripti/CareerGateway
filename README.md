# Career Gateway - AI Career Assistant

A Django web application built from the "Career Gateway: AI Career Assistant, Product and Integration Plan".
Idea: **AI for access, counsellors for guidance, professionals for experience.** The assistant helps
students explore and then connects them to a human counsellor. It does not replace one.

## What is built (mapped to the plan)

| Plan section | What exists |
|---|---|
| 1-3 Positioning, first conversation | "Career Assistant" with 7 starting options |
| 4 Student profile | Profile page (education, interests, skills, goals, location, budget, exams) |
| 5-6 Career discovery and explanation | Career pages with structured information and FAQs; transparent matching with reasons |
| 7 College recommendation | College and course database, rule-based matching (hard limits exclude with a reason, preferences only reorder, unknown data flagged, partner status disclosed) |
| 8 Counsellor handoff | Seven trigger situations and a counsellor request form |
| 9 Mentors | Mentor profiles for ten professions, "request a session" |
| 10 Opportunities | Scholarships, internships, competitions and more, matched on eligibility, level, location and deadline |
| 11 School version | School programs page, registration with minor-privacy safeguards, staff dashboard (counts only) |
| 12 Architecture | /how-it-works/ page |
| 13 Knowledge base and RAG | Controlled knowledge base, retrieval, free LLM writes the answer from the retrieved records only |
| 14 Admin dashboard | Lead dashboard, counsellor assignment, shortlist, application status |
| 15 Revenue | Tier labels only (free, lead, paid, admission, long-term). No payments |
| 16 MVP technology | Python/Django, chat widget (mobile responsive), SQLite or PostgreSQL via DATABASE_URL, free LLM (Gemini or Ollama) |

## Honest limits (please read)

- **No separate vector database.** Meaning-based search uses Gemini embeddings stored in the project's own database (vectors as JSON, cosine similarity), combined with word-overlap ranking. If embeddings are off or the API fails, retrieval falls back to word overlap. A dedicated vector store such as pgvector is the production upgrade.
- **All colleges, opportunities and mentors in the demo are fictional** and labelled that way. Knowledge entries and career texts are **not verified** yet and are labelled that way.
- **No booking, payments, SMS or email sending.** Requests are recorded as leads. Pages say that nothing is booked.
- The language model can still make mistakes. It is told to answer only from the retrieved records and to say so when it cannot.
- Free AI services may use question text to improve their products, so the pages ask users not to enter personal details. Only the question and public record text are sent to the model, never profile or contact data.
- Gradual profile building (section 4) is done as guided questions: the Assistant page asks one profile question at a time, with Skip and a progress bar, and saves only what the student types. It is not free-text conversation, so the assistant does not extract details from sentences.
- School version has programs, registration and a dashboard, but no separate per-school environments or teacher accounts yet.

## Run it locally (Windows PowerShell)

```
cd C:\CareerGateway
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then edit .env (set DJANGO_SECRET_KEY)
python manage.py migrate
python manage.py seed_careers
python manage.py seed_knowledge
python manage.py seed_demo_colleges
python manage.py seed_demo_opportunities
python manage.py seed_demo_mentors
python manage.py seed_demo_school_programs
python manage.py createsuperuser
python manage.py runserver
```

Generate a secret key with:
`python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`

## Free AI answers

Set these in `.env` (never commit it):

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key          # free key from https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite
```

Or run a local model with Ollama: `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=llama3.2`.
With `LLM_PROVIDER=none` the site still works and shows retrieved records only.
Model names change over time; check Google AI Studio for the free models on your account.

Prove it works (calls the real model and checks the answer is not copied text):

```
python manage.py check_llm
```

## Tests

```
python manage.py test core
```

The suite uses a mocked model, so it never calls the internet or uses your quota.

## Staff pages

Log in as a staff user: Lead Dashboard (/staff/leads/), School Dashboard (/staff/school/), and the admin (/admin/) for records.

## Deploy

See DEPLOY.md.
