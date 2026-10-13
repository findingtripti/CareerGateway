# PROJECT STATE CHECKPOINT — Career Gateway

**Date:** 2026-10-11 | **Current phase:** Phase 1 complete (pending final commit of tests); next is Phase 2 | **Source of truth:** original PDF "Career Gateway — AI Career Assistant: Product & Integration Plan" (18 sections)

## 1. Sources inspected (evidence)
- Original PDF (read fully, 18 sections). Both uploaded copies are byte-identical.
- CareerGateway.zip (source snapshot). It has no `.git` folder, no `requirements.txt`, no `db.sqlite3`.
- Last known Git checkpoint (from your notes, NOT verified from the zip): `main`, `02bad77`, repo `findingtripti/CareerGateway`.
- Commands run on a COPY of the zip (Django 5.2): `manage.py check` → no issues. `makemigrations --check` → no changes (models match migrations 0001–0004). `manage.py test` → 0 tests ran.

## 2. Confirmed stack (actual) vs PDF
| Item | Actual now | PDF §16 | Gap |
|---|---|---|---|
| Backend | Python + Django 5.2 | Python or Node | OK |
| DB | SQLite | PostgreSQL | GAP (migrate later, Phase 18 or earlier) |
| Frontend | Django templates | Chat widget, mobile responsive | Assistant is a form, not a chat widget |
| AI | none (keyword rules) | LLM + RAG + embeddings | NOT STARTED |
| CRM/booking/notifications | none | required | NOT STARTED |

## 3. Active vs backup files
- Active (routed): `core/views.py`, `core/urls.py`, templates home/login/signup/profile/careers/assistant.
- Historical backups (not routed): `core/views_backup.py`, `core/views_phase3_backup.py`, `core/urls_phase3_backup.py`, `core/templates/core/careers_backup.html`. Do not copy them over active files.

## 4. Existing models (verified from models.py)
- `StudentProfile` (OneToOne user): full_name, age, current_education, academic_background, subjects_and_interests, skills, career_interests, preferred_location, budget, entrance_exams, career_goals.
- `College`: name, location, website, description, is_verified, created_at.
- `Course` (FK College): name, duration, eligibility, fees, entrance_exam, admission_process.
- `Opportunity`: title, opportunity_type, description, eligibility, location, application_url, deadline, is_verified, created_at.
- Missing vs PDF §7: College has no scholarships, hostel, placement, partner status. No source or verified-date fields anywhere.

## 5. Requirements register (from PDF, stable IDs)
Status key: NS = not started, PI = partially implemented (code exists, not fully matching PDF), NT = implemented but not tested (no automated tests exist).

| ID | PDF § | Requirement | Status | Evidence / gap |
|---|---|---|---|---|
| REQ-01 | 1 | AI supports counselling; named "Career Assistant/Guide/Gateway Advisor"; flow Student→AI→Understand→Guide→Recommend→Counsellor | PI | Page exists as "Career Assistant"; no counsellor step |
| REQ-02.1 | 2 | Understand education level/background | PI | Profile form only |
| REQ-02.2 | 2 | Ask interests, goals, strengths, preferences | PI | One interest box + priority dropdown |
| REQ-02.3 | 2 | Understand location and budget constraints | PI | Stored in profile, not used in matching |
| REQ-02.4 | 2 | Explore suitable career paths | PI | 4 hardcoded careers |
| REQ-02.5 | 2 | Explain courses, degrees, pathways | NS | |
| REQ-02.6 | 2 | Suggest colleges from verified DB | NS | Models exist, no logic/UI |
| REQ-02.7 | 2 | Find scholarships and opportunities | NS | Model exists, no UI |
| REQ-02.8 | 2 | Answer common admission questions | NS | |
| REQ-02.9 | 2 | Recommend human counselling when appropriate | NS | |
| REQ-02.10 | 2 | Capture and qualify leads | NS | |
| REQ-03 | 3 | Welcome message + 7 starting options (career, course, colleges, scholarships, talk to professional, roadmap, "I don't know") | NS | Assistant has a different greeting, no option buttons |
| REQ-04 | 4 | Profile built gradually by the bot (10 fields) | PI | Fields exist; gradual conversational capture missing |
| REQ-05 | 5 | Discovery mode: explore several options, not one "best"; student picks one to go deeper | PI | Top-3 shown; no drill-down choice |
| REQ-06 | 6 | Career card with 10 fields (what they do, education, exams, skills, pathway, roles, higher education, work environments, insights, FAQs) + next step to counsellor/mentor | PI | Has ~6 of 10; missing higher education, work environments, insights, FAQs; no counsellor/mentor link |
| REQ-07.1 | 7 | College DB fields (11) | PI | Missing scholarships, hostel, placement, partner status |
| REQ-07.2 | 7 | Matching: Profile→Course→Eligibility→Budget→Location→Preferences→Colleges, from DB not LLM | NS | |
| REQ-07.3 | 7 | Disclose partner/commercial relationship | NS | No partner field |
| REQ-08 | 8 | Counsellor handoff on 7 triggers + suggested message | NS | |
| REQ-09 | 9 | Mentor matching + book session | NS | |
| REQ-10 | 10 | Opportunity finder, 9 types, matching on eligibility/level/location/interests/deadline | PI | Model has types, deadline; no UI/matching; "Career programs" type missing |
| REQ-11 | 11 | School version (8 items) + minor privacy by design | NS | |
| REQ-12 | 12 | AI + human architecture chain incl. Recommendation Engine | NS | |
| REQ-13 | 13 | Controlled knowledge base (11 content types) + RAG | NS | |
| REQ-14 | 14 | Admin dashboard: lead journey (9 items) | NS | Django admin only manages 4 models |
| REQ-15 | 15 | Revenue tiers (Free/Lead/Paid/Admission/Long-term) | NS | |
| REQ-16 | 16 | MVP tech (chat widget, PostgreSQL, LLM+RAG, CRM, booking, notifications) | NS/PI | See section 2 |
| REQ-17 | 17 | Bot never pretends to replace counsellor | PI | Assistant text says explore/compare; no explicit disclaimer or handoff |
| REQ-18 | 18 | Product vision statement | NS | Not shown on site |

Nothing above is marked "Tested": the project has 0 automated tests.

## 6. Audit findings (existing code)
Working per your report, unverified by me in a browser: home, signup, login, logout, profile, careers, assistant. Django check passes.

Issues found in code:
1. Career data (4 careers, keywords, next steps) is hardcoded and duplicated in `career_exploration` and `career_assistant`. It must move to database models (PDF §13: controlled knowledge base).
2. `SECRET_KEY` is hardcoded in settings.py, `DEBUG=True`, `ALLOWED_HOSTS=[]`. Must move to environment variables before any deployment.
3. No `requirements.txt`.
4. Profile view only overwrites a field when the new value is non-empty, so a student cannot clear a field.
5. Signup does not use Django's `UserCreationForm` or password validators (weak passwords accepted). Login ignores `?next=`.
6. `/careers/` is public but personalises when logged in; fine, but the match "score" is only a keyword count (do not present it as a suitability score).
7. `tests.py` is empty.
8. Backup files clutter `core/`.

## 7. Differentiation Ledger (hypotheses only, nothing implemented yet)
| Feature | PDF link | Status |
|---|---|---|
| Transparent recommendation reasoning (why / verified / unknown / trade-offs / partner disclosure) | REQ-07.2, 07.3 | Hypothesis |
| Data freshness fields (source, verified_on) on College/Course/Opportunity | REQ-07.1, 10 | Hypothesis |
| Human handoff based on the 7 PDF triggers | REQ-08 | Hypothesis |
| Pathway comparison, what-if, evidence-linked roadmap | REQ-05, 06 | Not selected yet (revisit after Phase 5) |

## 8. Previously agreed plan vs this PDF
No earlier planning notes or lean canvas were supplied beyond the continuation prompt, so no other prior decisions are recorded. The prompt's baseline (Django, `core` app, Phase 3 commit) is accepted as the starting point. Master Prompt V2 numbered phases from environment setup; because setup, auth, profile and a basic assistant already exist, this checkpoint follows the continuation prompt's phase list and keeps V2's rules (PDF labels, ledger, small verified steps).

## 9. Roadmap order (all PDF items covered)
0 Audit → 1 Foundation (env vars, requirements.txt, tests, cleanup) → 2–3 Polish existing pages → 4 Career knowledge base models (REQ-05/06/13) → 5 RAG → 6 AI assistant with first-conversation options (REQ-03/04) → 7 Recommendations → 8 Colleges/courses (REQ-07) → 9 Opportunities (REQ-10) → 10 Counsellor handoff + CRM (REQ-08/14) → 11 Mentors (REQ-09) → 12 School (REQ-11) → 13 Admin dashboard → 14 Revenue (REQ-15) → 15 Notifications → 16–19 UX, testing, deployment (PostgreSQL), docs.

## 10. Phase 1 log (verified by user terminal output)
| Step | What | Evidence |
|---|---|---|
| 1 | Git state verified; `requirements.txt` created (asgiref 3.12.1, Django 5.2.18, sqlparse 0.6.0, tzdata 2026.5; later + python-dotenv 1.2.4) | `git status` clean at `02bad77`; `type requirements.txt` output |
| 2 | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` read from `.env` via python-dotenv; `.env.example` added; `.gitignore` allows `.env.example`; new secret key generated (old key was public in Git history, so it must stay retired) | `manage.py check` no issues; site and login worked; commit `31ad931` pushed |
| 3 | 4 backup files moved to `_archive/` with `git mv` | `git status` showed 4 renames; commit `f1135fb` pushed; pages opened OK |
| 4 | 19 automated tests in `core/tests.py` (public pages, signup, login/logout, profile, assistant) | `python manage.py test` → `Ran 19 tests ... OK` |

Environment variable names (values never committed): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`.
Run: `.\.venv\Scripts\Activate.ps1` → `python manage.py runserver`. Test: `python manage.py test`.

## 11. Known limitations of the tests (honest scope)
The tests lock in CURRENT behaviour, not ideal behaviour. For example, profile fields can still not be cleared, and weak passwords are still accepted at signup. These are Phase 2 fixes and the related tests will change then. No tests exist yet for models, careers content or admin. Tested locally only, not in production. Database is still SQLite (PDF §16 asks for PostgreSQL).

## 12. Exact next task
1. Commit the tests (`git add core/tests.py PROJECT_CHECKPOINT.md`, commit, push).
2. Phase 2, Step 1: signup hardening using Django's password validators and `UserCreationForm`-style checks (REQ-02.1 foundation), with tests written first.

## 13. Milestone 3 - Colleges (PDF section 7) [REQ-02.6, 07.1, 07.2, 07.3]
- College gains: scholarships, hostel, placement, last_verified, source_note, is_demo, is_published, partner_status, partner_disclosure. Course gains: min_education, related_careers.
- `core/college_matching.py`: HARD rules (budget, education level) exclude with a stated reason; SOFT preferences (location, career interest) only reorder; unknown data is flagged, never excluded. Partner status never affects order. Stale = not verified in 365 days.
- Pages: /colleges/ (search, max fees), /colleges/<id>/, /colleges/recommend/ (login, what-if budget/location without saving).
- `seed_demo_colleges` adds FICTIONAL labelled demo data. Replace with verified data before real use.
- Tests: 108 passing in the build sandbox.
- Next: M4 opportunities (sec 10) and counsellor handoff / leads (sec 8). Plan to Wednesday: M4-M10 in CareerGateway_Plan_to_Wednesday.xlsx.

## 14. Milestone 4 - Opportunities and scholarships (PDF section 10) [REQ-10, 02.7]
- Opportunity gains: min_education, related_careers, last_verified, source_note, is_demo, is_published; new type "Career Program" (PDF lists it). Migration 0007.
- `core/opportunity_matching.py`: HARD = deadline passed, education below requirement (reason shown); SOFT = location, career interest (reorder only); UNKNOWN = no deadline / unknown education (flagged). Closing soon = 14 days or less.
- Pages: /opportunities/ (search, type filter, expired labelled), /opportunities/<id>/, /opportunities/for-me/ (login). Assistant "Scholarships" option is now available.
- `seed_demo_opportunities` adds FICTIONAL labelled data (one already expired on purpose).
- Tests: 129 passing in the build sandbox.
- Next: M5 counsellor handoff on the 7 triggers + enquiry/lead capture (sec 8, 14).

## 15. Milestone 5 - Counsellor handoff and leads (PDF sections 8, 14, 15) [REQ-02.9, 02.10, 08, 14 (part), 15 (labels)]
- `core/handoff.py`: the seven PDF section 8 situations, whole-phrase matching, so the reason is always shown. Two or more reasonable options also triggers the PDF's suggested message word for word. It only SUGGESTS a counsellor.
- `Lead` model (migration 0008): lead types match the PDF section 14 list (student, career, college enquiries, counselling and mentor requests, admission leads), stage, counsellor assignment, college shortlist, application status, consent, tier label (section 15). No booking, no payment.
- Pages: /counsellor/request/, college and career "Ask" forms, /requests/ (own leads only), /staff/leads/ (staff only dashboard with lead journey).
- Consent is required, contact needs a valid email or phone, message capped at 2000 characters, thanks page says nothing is booked.
- Admin: Lead list with filters and actions (contacted, qualified, assign to me).
- Honest limits: no email or SMS is sent yet (M10). Counsellor assignment is a manual admin action. Tier is a label only.
- Tests: 162 passing in the build sandbox.
- Next: M7 mentors (sec 9), then M8 knowledge base, M9 school version, M10 wrap-up.

## 16. Milestone 7 - Mentors (PDF section 9) plus home navbar and timezone fixes [REQ-09]
- Mentor model (migration 0009): the ten professions the PDF lists, linked to careers, with verification, demo and publish flags. A private contact_note is never shown to students. Lead gains related_mentor.
- Flow from the PDF: career profile -> mentors for that career -> ask for a session. Career pages list matching mentors. /mentors/ filters by career and profession.
- "Ask for a session" saves a mentor_request lead (tier label Paid). It books nothing, contacts no mentor and takes no payment. Pages say so.
- `seed_demo_mentors` adds clearly FICTIONAL mentors. Real mentors need consent and verification before launch.
- Home page now uses the same links as the rest of the site (it had its own older navbar). TIME_ZONE changed to Asia/Kolkata (dashboard times were shown in UTC).
- Tests: 185 passing in the build sandbox.
- Next: M8 knowledge base and retrieval answers (sec 13), M9 school version (sec 11), M10 wrap-up.

## 17. Milestone 8 - Knowledge base and "Ask Career Gateway" (PDF sections 13, 2, 16) [REQ-13, 02.8, 16 (chat widget)]
- `KnowledgeEntry` model (migration 0010) covers the PDF section 13 types that have no table of their own: FAQs, course information, eligibility, admission processes, scholarships, entrance exams, career roadmaps, school programs. Careers, colleges, opportunities and mentors are searched from their own tables.
- `core/retrieval.py` is the retrieval step of the PDF's RAG pattern: word-overlap ranking over published records, with title > keyword > body weighting. Every result shows its source record, the matched words, a verified or not-verified label, a demo label and the last-verified date. Nothing is generated.
- IMPLEMENTATION DECISION: no LLM and no embeddings yet (needs an API key and cost). FUTURE: an LLM could rewrite the retrieved passages, but must answer only from them.
- /ask/ page, /ask/api/ JSON endpoint and a floating chat widget on every page (plain JavaScript, works without JavaScript through a link). No result means "we could not find this and will not guess", with a counsellor link. Counsellor triggers in the question are suggested.
- `seed_knowledge` adds 10 general entries with no dates, fees or college rules, all marked NOT verified, with a note that a counsellor must review them.
- Tests: 215 passing in the build sandbox.
- Next: M9 school version with minor-privacy rules (sec 11), M10 wrap-up (README, viva notes, architecture sec 12, PostgreSQL setting, notifications, final tests).

## 18. Milestone 9 - School version, widget fixes, ranking (PDF section 11) [REQ-11]
- `SchoolProgram` and `SchoolRegistration` (migration 0011). Programs are listings of assessment sessions, workshops, career talks, counselling sessions and mentor sessions. Registration records interest only; nothing is booked.
- MINOR PRIVACY (PDF section 11): registration holds no phone, email or address, only the school name and consent flags. A student who says they are under 18 must tick parent or guardian consent. The staff dashboard (/staff/school/, staff only) shows counts by program and school, never names or contacts. Individual rows are read-only in the admin.
- Pages: /school/ (public overview linking assistant, careers, mentors, opportunities, counsellor request), /school/<id>/register/ (login needed), /staff/school/. "Schools" added to the navbar.
- `seed_demo_school_programs` adds 3 FICTIONAL programs.
- Honest scope: the "career assessment" is the existing Career Assistant (an exploration activity, not a psychometric test). No bulk school onboarding or teacher accounts yet (future work).
- Chat widget: panel opens above the button; typing clears the old answer; "You asked: ..." line; Clear button; a request counter ignores late replies to older questions.
- Retrieval ranking: generic site words (college, course, career, ...) now count 0.3 instead of 1 in body/keyword matches, so records that match only a generic word rank below records matching a specific word. Titles still count 3.
- Tests: 250 passing in the build sandbox.
- Next: M10 wrap-up (README, viva notes, architecture sec 12, PostgreSQL setting, notifications, final tests).
