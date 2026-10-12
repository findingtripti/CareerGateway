"""Starter career content for `python manage.py seed_careers`.

HONESTY NOTE: this text was drafted from general knowledge for this project.
It has NOT been checked against official sources, so every career is seeded
as "needs_verification". Staff should review and correct each career in the
Django admin, add sources, and then mark it "verified".
"""

SOURCE_NOTE = (
    "Drafted from general knowledge for this project. Not yet checked "
    "against official sources; verify requirements before relying on them."
)

CAREERS = [
    {
        "title": "Software Development",
        "slug": "software-development",
        "summary": "Design, build, test, and maintain software applications.",
        "what_professionals_do": (
            "Build, test, debug, and maintain software applications with "
            "a team."
        ),
        "required_education": (
            "A Computer Science or related degree is a common route. "
            "Skill-based learning backed by projects is another."
        ),
        "entrance_exams": (
            "Some engineering programmes use JEE or institution-specific "
            "entrance tests. Other learning routes may not require a "
            "separate entrance exam. Check current requirements."
        ),
        "important_skills": "Python, programming, problem-solving",
        "career_pathway": (
            "Learn programming fundamentals, build small projects, then "
            "move to internships or junior developer roles."
        ),
        "possible_roles": (
            "Software Developer, Web Developer, Application Developer"
        ),
        "higher_education_options": (
            "Master's programmes in computer science or specialised areas "
            "such as AI or systems."
        ),
        "work_environments": (
            "Software companies, startups, and IT services firms, often "
            "in team-based or remote settings."
        ),
        "professional_insights": (
            "A lot of the work is reading and fixing existing code and "
            "working with a team, not only writing new programs."
        ),
        "first_step": (
            "Build a small Python project, practise problem-solving, and "
            "learn Git and GitHub."
        ),
        "coding_intensity": "high",
        "priority_tag": "problem_solving",
        "keywords": (
            "software, developer, programming, coding, code, python, java, "
            "web, application, computer science, problem solving"
        ),
        "faqs": [
            ("Do I need a degree to become a developer?",
             "A degree is a common route but not the only one. Many "
             "employers also look at projects and skills. Requirements "
             "vary by employer."),
            ("Which language should a beginner start with?",
             "Python is a common beginner choice, but the best choice "
             "depends on your goal, such as websites, apps or data."),
        ],
    },
    {
        "title": "Data Science",
        "slug": "data-science",
        "summary": (
            "Use data, statistics, and computing to find patterns and "
            "support decisions."
        ),
        "what_professionals_do": (
            "Analyse datasets, find patterns, create visualisations, and "
            "support data-driven decisions."
        ),
        "required_education": (
            "A degree with statistics, mathematics or computing, plus "
            "practical data projects."
        ),
        "entrance_exams": (
            "Depending on the programme, examples may include JEE, CUET, "
            "or institution-specific admission tests. Requirements vary."
        ),
        "important_skills": "Python, statistics, SQL, data analysis",
        "career_pathway": (
            "A relevant degree plus statistics, programming, and data "
            "projects. Entry roles often start as a data analyst."
        ),
        "possible_roles": (
            "Data Analyst, Junior Data Scientist, "
            "Business Intelligence Analyst"
        ),
        "higher_education_options": (
            "Master's programmes in data science, statistics or related "
            "fields."
        ),
        "work_environments": (
            "Technology, finance, healthcare, e-commerce and research "
            "organisations, in office, hybrid or remote settings."
        ),
        "professional_insights": (
            "A large part of the work is cleaning and understanding data, "
            "not building models."
        ),
        "first_step": (
            "Practise Python, learn basic statistics, and analyse a small "
            "dataset."
        ),
        "coding_intensity": "medium",
        "priority_tag": "data",
        "keywords": (
            "data, analytics, analysis, statistics, sql, machine learning, "
            "math, mathematics, research"
        ),
        "faqs": [
            ("Is data science only for people who are strong in maths?",
             "Comfort with statistics and basic mathematics helps, but it "
             "can be built step by step through practice."),
            ("What is the difference between a data analyst and a data "
             "scientist?",
             "Analysts mostly describe and explain data to support "
             "decisions, while scientists more often build predictive "
             "models. Job titles differ between employers."),
        ],
    },
    {
        "title": "Cybersecurity",
        "slug": "cybersecurity",
        "summary": (
            "Help protect systems, networks, and information from "
            "security threats."
        ),
        "what_professionals_do": (
            "Monitor systems, investigate security alerts, assess "
            "vulnerabilities, and help protect digital information."
        ),
        "required_education": (
            "IT or computing foundations, or a computer science degree, "
            "plus practical security learning."
        ),
        "entrance_exams": (
            "Depending on the programme, examples may include JEE, CUET, "
            "or institution-specific admission tests. Check the "
            "institution's requirements."
        ),
        "important_skills": (
            "Networking, operating systems, security fundamentals"
        ),
        "career_pathway": (
            "IT or computing foundations plus practical learning in "
            "authorised security labs, then junior analyst roles."
        ),
        "possible_roles": "Security Analyst, SOC Analyst, Security Engineer",
        "higher_education_options": (
            "Master's programmes in cybersecurity or information "
            "security. Professional certifications are also common."
        ),
        "work_environments": (
            "Companies, banks, government agencies and security "
            "consultancies. Some roles involve shift or on-call work."
        ),
        "professional_insights": (
            "Much of the work is monitoring, investigating alerts and "
            "documenting findings, not only 'hacking'."
        ),
        "first_step": (
            "Learn networking fundamentals, Linux basics, and practise in "
            "a legal beginner cybersecurity lab."
        ),
        "coding_intensity": "medium",
        "priority_tag": "security",
        "keywords": (
            "cybersecurity, cyber security, security, network, networking, "
            "ethical hacking, linux, system, privacy"
        ),
        "faqs": [
            ("Is cybersecurity only ethical hacking?",
             "No. Roles include monitoring, incident response, risk "
             "assessment and policy as well as testing systems."),
            ("Is it legal to practise hacking skills at home?",
             "Only on systems you own or have written permission to test. "
             "Use authorised training labs."),
        ],
    },
    {
        "title": "UI/UX Design",
        "slug": "ui-ux-design",
        "summary": (
            "Research user needs and design useful, accessible digital "
            "experiences."
        ),
        "what_professionals_do": (
            "Understand user needs, create wireframes and prototypes, "
            "test designs, and improve digital experiences."
        ),
        "required_education": (
            "Design or related education, or self-directed learning, plus "
            "a portfolio of projects."
        ),
        "entrance_exams": (
            "Some design programmes use UCEED, NID DAT, or "
            "institution-specific admission processes. Check current "
            "eligibility and exam requirements."
        ),
        "important_skills": "Design thinking, user research, prototyping",
        "career_pathway": (
            "Learn user research, wireframing and prototyping, build a "
            "portfolio, then move to junior designer roles."
        ),
        "possible_roles": "UI Designer, UX Designer, Product Designer",
        "higher_education_options": (
            "Master's programmes in design or human-computer interaction."
        ),
        "work_environments": (
            "Product companies, design studios, agencies and startups, "
            "often with remote options."
        ),
        "professional_insights": (
            "Hiring often relies on a portfolio that shows your process, "
            "not only the final screens."
        ),
        "first_step": (
            "Study usability principles and create a simple wireframe for "
            "a student-focused app."
        ),
        "coding_intensity": "low",
        "priority_tag": "creativity",
        "keywords": (
            "design, ui, ux, creative, creativity, visual, art, "
            "user experience, product design, prototyping"
        ),
        "faqs": [
            ("Do UI/UX designers need to code?",
             "Not usually, but understanding basic HTML and CSS helps you "
             "work with developers."),
            ("What goes into a design portfolio?",
             "A few projects showing the problem, your research, the "
             "ideas you tried and the result."),
        ],
    },
    {
        "title": "Product Management",
        "slug": "product-management",
        "summary": (
            "Decide what a product should do by working with users, "
            "designers and engineers."
        ),
        "what_professionals_do": (
            "Study user needs, set priorities, write requirements, and "
            "coordinate teams to deliver a product."
        ),
        "required_education": (
            "There is no single required degree. Many people come from "
            "engineering, business or design backgrounds."
        ),
        "entrance_exams": (
            "There is no specific entrance exam for the role. Some "
            "management programmes use exams such as CAT. Check current "
            "requirements."
        ),
        "important_skills": (
            "Communication, user research, prioritisation, basic data "
            "analysis, understanding of technology"
        ),
        "career_pathway": (
            "Often begins in another role such as engineering, design or "
            "analysis, then moves to associate or junior product roles."
        ),
        "possible_roles": (
            "Associate Product Manager, Product Analyst, Product Manager"
        ),
        "higher_education_options": (
            "An MBA or other management programme is one option, not a "
            "requirement."
        ),
        "work_environments": (
            "Software and internet companies and startups, with a lot of "
            "meetings and cross-team work."
        ),
        "professional_insights": (
            "Product managers influence decisions through communication "
            "rather than direct authority, and rarely build the product "
            "themselves."
        ),
        "first_step": (
            "Pick an app you use, write down its main user problems, and "
            "decide how you would prioritise fixing them."
        ),
        "coding_intensity": "low",
        "priority_tag": "",
        "keywords": (
            "product management, product manager, product, strategy, "
            "business, users, planning, leadership, management"
        ),
        "faqs": [
            ("Do product managers need to code?",
             "Not usually, but understanding how software is built helps "
             "when working with engineers."),
            ("Can a fresher become a product manager?",
             "Entry roles exist, but many people move into product "
             "management after another role. Opportunities vary by "
             "company."),
        ],
    },
    {
        "title": "Cloud Computing",
        "slug": "cloud-computing",
        "summary": (
            "Design, run and secure computing systems delivered over the "
            "internet."
        ),
        "what_professionals_do": (
            "Set up and manage servers, storage and networks on cloud "
            "platforms, and keep them reliable and secure."
        ),
        "required_education": (
            "A computer science, IT or related degree, or equivalent "
            "practical learning."
        ),
        "entrance_exams": (
            "Entrance tests depend on the degree programme, for example "
            "JEE or institution tests for engineering. Cloud providers "
            "also offer optional professional certifications."
        ),
        "important_skills": (
            "Linux, networking, one cloud platform, scripting, security "
            "basics"
        ),
        "career_pathway": (
            "IT or computing foundations, practical cloud labs, then "
            "junior cloud, support or DevOps roles."
        ),
        "possible_roles": (
            "Cloud Support Engineer, Cloud Engineer, DevOps Engineer"
        ),
        "higher_education_options": (
            "Master's programmes in computer science, or certifications "
            "from cloud providers."
        ),
        "work_environments": (
            "Technology companies, IT services firms, and large "
            "organisations running online services. Some roles involve "
            "on-call work."
        ),
        "professional_insights": (
            "Cost and reliability matter as much as technical setup. "
            "Mistakes can be expensive on pay-as-you-go platforms."
        ),
        "first_step": (
            "Learn Linux and networking basics, then try the free tier of "
            "one cloud platform with a small project, and watch for "
            "charges."
        ),
        "coding_intensity": "medium",
        "priority_tag": "problem_solving",
        "keywords": (
            "cloud, aws, azure, devops, linux, servers, infrastructure, "
            "networking, system"
        ),
        "faqs": [
            ("Do I need certifications?",
             "They can help show your skills but are usually optional. "
             "Employers vary."),
            ("Is cloud computing only for programmers?",
             "Scripting helps, but many roles focus more on systems, "
             "networking and operations than on building applications."),
        ],
    },
    {
        "title": "Digital Forensics",
        "slug": "digital-forensics",
        "summary": (
            "Collect and examine digital evidence from computers, phones "
            "and networks."
        ),
        "what_professionals_do": (
            "Recover and analyse data from devices to find out what "
            "happened, and document findings so they can be used in "
            "investigations."
        ),
        "required_education": (
            "Computer science, IT, cybersecurity or forensic science "
            "degrees are common routes."
        ),
        "entrance_exams": (
            "This depends on the degree programme. Check each "
            "institution's requirements."
        ),
        "important_skills": (
            "Operating systems, file systems, networking, careful "
            "documentation, attention to detail"
        ),
        "career_pathway": (
            "Computing or forensic science foundations, practice with "
            "authorised forensic tools and sample images, then junior "
            "analyst roles."
        ),
        "possible_roles": (
            "Digital Forensic Analyst, Incident Response Analyst, "
            "Forensic Examiner"
        ),
        "higher_education_options": (
            "Master's programmes in digital forensics or cybersecurity."
        ),
        "work_environments": (
            "Law enforcement agencies, forensic labs, corporate security "
            "teams and consulting firms. The work can be sensitive and "
            "detail-heavy."
        ),
        "professional_insights": (
            "Documentation and a clear record of how evidence was handled "
            "matter as much as technical skill, because findings may be "
            "reviewed in legal processes."
        ),
        "first_step": (
            "Learn how files and operating systems store data, and "
            "practise on public sample disk images made for training."
        ),
        "coding_intensity": "medium",
        "priority_tag": "security",
        "keywords": (
            "forensics, forensic, investigation, evidence, security, "
            "police, cybercrime, cyber crime"
        ),
        "faqs": [
            ("Is digital forensics the same as cybersecurity?",
             "They overlap, but forensics focuses on investigating what "
             "already happened, while security focuses on preventing and "
             "detecting problems."),
            ("Do digital forensics roles exist outside the police?",
             "Yes. Companies, consultancies and labs also hire for this "
             "work. Availability varies by location."),
        ],
    },
    {
        "title": "Technology Consulting",
        "slug": "technology-consulting",
        "summary": (
            "Advise organisations on how to use technology to solve "
            "business problems."
        ),
        "what_professionals_do": (
            "Understand a client's problem, analyse options, recommend "
            "technology solutions and help teams put them in place."
        ),
        "required_education": (
            "There is no single required degree. Engineering, computer "
            "science, business and related degrees are common."
        ),
        "entrance_exams": (
            "There is no specific exam for the role. Entry to degrees and "
            "some management programmes depends on each institution's "
            "requirements."
        ),
        "important_skills": (
            "Communication, problem structuring, presentation, basic "
            "technical understanding, teamwork"
        ),
        "career_pathway": (
            "A degree plus internships or projects, then analyst roles at "
            "consulting or IT services firms."
        ),
        "possible_roles": (
            "Technology Analyst, Business Analyst, Associate Consultant"
        ),
        "higher_education_options": (
            "An MBA or a specialised master's programme is one option."
        ),
        "work_environments": (
            "Consulting and IT services firms, often with client visits, "
            "travel and project deadlines."
        ),
        "professional_insights": (
            "Much of the work is communicating and structuring problems "
            "for clients, not only technical work."
        ),
        "first_step": (
            "Practise explaining a technical idea to a non-technical "
            "person in two minutes, and write one-page summaries of "
            "business problems."
        ),
        "coding_intensity": "low",
        "priority_tag": "",
        "keywords": (
            "consulting, consultant, business analyst, advisory, strategy, "
            "technology, communication, clients"
        ),
        "faqs": [
            ("Do consultants need strong coding skills?",
             "Usually not, but you need enough technical understanding to "
             "advise on technology."),
            ("Do consulting firms only hire from top colleges?",
             "Hiring practices vary by firm. Some recruit mainly from "
             "selected institutions, so check each firm's current "
             "approach."),
        ],
    },
]
