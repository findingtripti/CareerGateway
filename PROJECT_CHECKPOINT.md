

Project checkpoint · MD
PROJECT STATE CHECKPOINT — Career Gateway
Date: 2026-10-11 | Current phase: Phase 1 complete (pending final commit of tests); next is Phase 2 | Source of truth: original PDF "Career Gateway — AI Career Assistant: Product & Integration Plan" (18 sections)

1. Sources inspected (evidence)
Original PDF (read fully, 18 sections). Both uploaded copies are byte-identical.
CareerGateway.zip (source snapshot). It has no .git folder, no requirements.txt, no db.sqlite3.
Last known Git checkpoint (from your notes, NOT verified from the zip): main, 02bad77, repo findingtripti/CareerGateway.
Commands run on a COPY of the zip (Django 5.2): manage.py check → no issues. makemigrations --check → no changes (models match migrations 0001–0004). manage.py test → 0 tests ran.
2. Confirmed stack (actual) vs PDF
Item	Actual now	PDF §16	Gap
Backend	Python + Django 5.2	Python or Node	OK
DB	SQLite	PostgreSQL	GAP (migrate later, Phase 18 or earlier)
Frontend	Django templates	Chat widget, mobile responsive	Assistant is a form, not a chat widget
AI	none (keyword rules)	LLM + RAG + embeddings	NOT STARTED
CRM/booking/notifications	none	required	NOT STARTED
3. Active vs backup files
Active (routed): core/views.py, core/urls.py, templates home/login/signup/profile/careers/assistant.
Historical backups (not routed): core/views_backup.py, core/views_phase3_backup.py, core/urls_phase3_backup.py, core/templates/core/careers_backup.html. Do not copy them over active files.
4. Existing models (verified from models.py)
StudentProfile (OneToOne user): full_name, age, current_education, academic_background, subjects_and_interests, skills, career_interests, preferred_location, budget, entrance_exams, career_goals.
College: name, location, website, description, is_verified, created_at.
Course (FK College): name, duration, eligibility, fees, entrance_exam, admission_process.
Opportunity: title, opportunity_type, description, eligibility, location, application_url, deadline, is_verified, created_at.
Missing vs PDF §7: College has no scholarships, hostel, placement, partner status. No source or verified-date fields anywhere.
5. Requirements register (from PDF, stable IDs)
Status key: NS = not started, PI = partially implemented (code exists, not fully matching PDF), NT = implemented but not tested (no automated tests exist).

ID	PDF §	Requirement	Status	Evidence / gap
REQ-01	1	AI supports counselling; named "Career Assistant/Guide/Gateway Advisor"; flow Student→AI→Understand→Guide→Recommend→Counsellor	PI	Page exists as "Career Assistant"; no counsellor step
REQ-02.1	2	Understand education level/background	PI	Profile form only
REQ-02.2	2	Ask interests, goals, strengths, preferences	PI	One interest box + priority dropdown
REQ-02.3	2	Understand location and budget constraints	PI	Stored in profile, not used in matching
REQ-02.4	2	Explore suitable career paths	PI	4 hardcoded careers
REQ-02.5	2	Explain courses, degrees, pathways	NS	
REQ-02.6	2	Suggest colleges from verified DB	NS	Models exist, no logic/UI
REQ-02.7	2	Find scholarships and opportunities	NS	Model exists, no UI
REQ-02.8	2	Answer common admission questions	NS	
REQ-02.9	2	Recommend human counselling when appropriate	NS	
REQ-02.10	2	Capture and qualify leads	NS	
REQ-03	3	Welcome message + 7 starting options (career, course, colleges, scholarships, talk to professional, roadmap, "I don't know")	NS	Assistant has a different greeting, no option buttons
REQ-04	4	Profile built gradually by the bot (10 fields)	PI	Fields exist; gradual conversational capture missing
REQ-05	5	Discovery mode: explore several options, not one "best"; student picks one to go deeper	PI	Top-3 shown; no drill-down choice
REQ-06	6	Career card with 10 fields (what they do, education, exams, skills, pathway, roles, higher education, work environments, insights, FAQs) + next step to counsellor/mentor	PI	Has ~6 of 10; missing higher education, work environments, insights, FAQs; no counsellor/mentor link
REQ-07.1	7	College DB fields (11)	PI	Missing scholarships, hostel, placement, partner status
REQ-07.2	7	Matching: Profile→Course→Eligibility→Budget→Location→Preferences→Colleges, from DB not LLM	NS	
REQ-07.3	7	Disclose partner/commercial relationship	NS	No partner field
REQ-08	8	Counsellor handoff on 7 triggers + suggested message	NS	
REQ-09	9	Mentor matching + book session	NS	
REQ-10	10	Opportunity finder, 9 types, matching on eligibility/level/location/interests/deadline	PI	Model has types, deadline; no UI/matching; "Career programs" type missing
REQ-11	11	School version (8 items) + minor privacy by design	NS	
REQ-12	12	AI + human architecture chain incl. Recommendation Engine	NS	
REQ-13	13	Controlled knowledge base (11 content types) + RAG	NS	
REQ-14	14	Admin dashboard: lead journey (9 items)	NS	Django admin only manages 4 models
REQ-15	15	Revenue tiers (Free/Lead/Paid/Admission/Long-term)	NS	
REQ-16	16	MVP tech (chat widget, PostgreSQL, LLM+RAG, CRM, booking, notifications)	NS/PI	See section 2
REQ-17	17	Bot never pretends to replace counsellor	PI	Assistant text says explore/compare; no explicit disclaimer or handoff
REQ-18	18	Product vision statement	NS	Not shown on site
Nothing above is marked "Tested": the project has 0 automated tests.

6. Audit findings (existing code)
Working per your report, unverified by me in a browser: home, signup, login, logout, profile, careers, assistant. Django check passes.

Issues found in code:

Career data (4 careers, keywords, next steps) is hardcoded and duplicated in career_exploration and career_assistant. It must move to database models (PDF §13: controlled knowledge base).
SECRET_KEY is hardcoded in settings.py, DEBUG=True, ALLOWED_HOSTS=[]. Must move to environment variables before any deployment.
No requirements.txt.
Profile view only overwrites a field when the new value is non-empty, so a student cannot clear a field.
Signup does not use Django's UserCreationForm or password validators (weak passwords accepted). Login ignores ?next=.
/careers/ is public but personalises when logged in; fine, but the match "score" is only a keyword count (do not present it as a suitability score).
tests.py is empty.
Backup files clutter core/.
7. Differentiation Ledger (hypotheses only, nothing implemented yet)
Feature	PDF link	Status
Transparent recommendation reasoning (why / verified / unknown / trade-offs / partner disclosure)	REQ-07.2, 07.3	Hypothesis
Data freshness fields (source, verified_on) on College/Course/Opportunity	REQ-07.1, 10	Hypothesis
Human handoff based on the 7 PDF triggers	REQ-08	Hypothesis
Pathway comparison, what-if, evidence-linked roadmap	REQ-05, 06	Not selected yet (revisit after Phase 5)
8. Previously agreed plan vs this PDF
No earlier planning notes or lean canvas were supplied beyond the continuation prompt, so no other prior decisions are recorded. The prompt's baseline (Django, core app, Phase 3 commit) is accepted as the starting point. Master Prompt V2 numbered phases from environment setup; because setup, auth, profile and a basic assistant already exist, this checkpoint follows the continuation prompt's phase list and keeps V2's rules (PDF labels, ledger, small verified steps).

9. Roadmap order (all PDF items covered)
0 Audit → 1 Foundation (env vars, requirements.txt, tests, cleanup) → 2–3 Polish existing pages → 4 Career knowledge base models (REQ-05/06/13) → 5 RAG → 6 AI assistant with first-conversation options (REQ-03/04) → 7 Recommendations → 8 Colleges/courses (REQ-07) → 9 Opportunities (REQ-10) → 10 Counsellor handoff + CRM (REQ-08/14) → 11 Mentors (REQ-09) → 12 School (REQ-11) → 13 Admin dashboard → 14 Revenue (REQ-15) → 15 Notifications → 16–19 UX, testing, deployment (PostgreSQL), docs.

10. Phase 1 log (verified by user terminal output)
Step	What	Evidence
1	Git state verified; requirements.txt created (asgiref 3.12.1, Django 5.2.18, sqlparse 0.6.0, tzdata 2026.5; later + python-dotenv 1.2.4)	git status clean at 02bad77; type requirements.txt output
2	SECRET_KEY, DEBUG, ALLOWED_HOSTS read from .env via python-dotenv; .env.example added; .gitignore allows .env.example; new secret key generated (old key was public in Git history, so it must stay retired)	manage.py check no issues; site and login worked; commit 31ad931 pushed
3	4 backup files moved to _archive/ with git mv	git status showed 4 renames; commit f1135fb pushed; pages opened OK
4	19 automated tests in core/tests.py (public pages, signup, login/logout, profile, assistant)	python manage.py test → Ran 19 tests ... OK
| 5 | Phase 2: signup password validators (commit 88e4422), profile clear and safe validation (31aacee), login safe `?next=` (342e1cf) | user-run tests and browser checks |
| 6 | Milestone 1: shared `base.html`, styled login/signup (REQ-16 mobile responsive), assistant PDF §3 welcome text and 7 starting options in `core/assistant_options.py`, PDF §17 disclaimer. Unbuilt options say "not available yet" and never claim a booking | 47 tests OK in a verified copy of the latest zip; desktop and mobile screenshots checked; NOT yet run on the user's machine |

Environment variable names (values never committed): DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS. Run: .\.venv\Scripts\Activate.ps1 → python manage.py runserver. Test: python manage.py test.

11. Known limitations of the tests (honest scope)
The tests lock in CURRENT behaviour, not ideal behaviour. For example, profile fields can still not be cleared, and weak passwords are still accepted at signup. These are Phase 2 fixes and the related tests will change then. No tests exist yet for models, careers content or admin. Tested locally only, not in production. Database is still SQLite (PDF §16 asks for PostgreSQL).

12. Exact next task
Commit the tests (git add core/tests.py PROJECT_CHECKPOINT.md, commit, push).
Phase 2, Step 1: signup hardening using Django's password validators and UserCreationForm-style checks (REQ-02.1 foundation), with tests written first.
Claude finished the response
