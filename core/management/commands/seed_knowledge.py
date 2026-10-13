from datetime import date  # noqa: F401

from django.core.management.base import BaseCommand

from core.models import KnowledgeEntry

NOTE = (
    "General explanation written by the project team. It contains no "
    "college-specific dates, fees or rules. Needs review by a counsellor "
    "before launch."
)

# (title, type, content, keywords)
ENTRIES = [
    ("What is an entrance exam?", "entrance_exam",
     "An entrance exam is a test that a college or a programme uses to decide "
     "who gets admission. Some courses admit students only through an exam, "
     "some use school marks, and some use both. The exam body publishes the "
     "syllabus, pattern and dates on its official website, so always confirm "
     "them there.",
     "entrance, exam, test, admission, syllabus"),
    ("How do I prepare for an entrance exam?", "entrance_exam",
     "Start by reading the official syllabus and exam pattern. Practise with "
     "previous papers, keep a regular study schedule and review your mistakes. "
     "Check the official website for registration steps and deadlines.",
     "prepare, preparation, study, syllabus, practice"),
    ("How do I choose between two careers?", "faq",
     "List what each career involves day to day, the education it needs, and "
     "the skills you would use. Read the career profiles, talk to someone who "
     "works in each field, and try a small project. If you still cannot decide, "
     "a career counsellor can help you compare them.",
     "choose, choosing, decide, confused, compare, careers"),
    ("What is the difference between a diploma and a degree?", "course",
     "A diploma is usually a shorter, more focused programme. A degree is "
     "usually longer and broader. Eligibility, duration and recognition "
     "differ by institution, so check the details of each course.",
     "diploma, degree, difference, course, bachelor"),
    ("How do I read eligibility requirements?", "eligibility",
     "Look for the minimum education level, required subjects, minimum marks, "
     "any entrance exam and any age limit. If a requirement is unclear, ask "
     "the college directly before you apply.",
     "eligibility, requirements, criteria, minimum, marks, subjects"),
    ("What steps does a typical college admission have?", "admission_process",
     "Admission steps differ by college, but they often include checking "
     "eligibility, taking an entrance exam or using your marks, filling in an "
     "application, uploading documents, and then waiting for results or "
     "counselling. Always follow the official admission page of the college.",
     "admission, apply, application, process, steps, college"),
    ("What documents are usually needed for admission?", "admission_process",
     "Colleges commonly ask for mark sheets, an identity proof, passport-size "
     "photographs and certificates for any reservation or scholarship claim. "
     "The exact list is published by each college, so check it before applying.",
     "documents, certificates, marksheet, papers, admission"),
    ("How do scholarships usually work?", "scholarship",
     "Scholarships can be based on merit, financial need or a special "
     "category. Each one has its own eligibility rules and deadline. Apply "
     "only through the official page, and be careful of anyone asking for "
     "money to apply.",
     "scholarship, scholarships, funding, merit, need, deadline, apply"),
    ("How do I build a simple career roadmap?", "roadmap",
     "Choose a career to explore, find the education it needs, list the exams "
     "or skills involved, and break the path into small steps with a rough "
     "order. Review it as you learn more. A counsellor can help you turn it "
     "into a personal plan.",
     "roadmap, plan, steps, path, future, build"),
    ("What can a school career programme include?", "school_program",
     "A school programme can include career assessments, workshops, talks by "
     "professionals, counselling sessions and information about opportunities. "
     "Schools should protect student privacy and handle minors' data with "
     "extra care.",
     "school, programme, program, workshop, students, privacy"),
]


class Command(BaseCommand):
    help = (
        "Add general starter knowledge entries (not verified). Safe to run "
        "again: an entry with the same title is left untouched."
    )

    def handle(self, *args, **options):
        added = 0
        for title, kind, content, keywords in ENTRIES:
            _, created = KnowledgeEntry.objects.get_or_create(
                title=title,
                defaults={
                    "entry_type": kind,
                    "content": content,
                    "keywords": keywords,
                    "is_verified": False,
                    "source_note": NOTE,
                },
            )
            added += int(created)
        self.stdout.write(self.style.SUCCESS(
            f"{added} knowledge entry(ies) added, {len(ENTRIES) - added} already present."
        ))
