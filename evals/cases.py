"""Eval cases.

ANALYZER_CASES test the structured job-analysis mode. Each case has a short job
description and `expect_any`: O*NET categories where we expect at least one of
the model's mapped skills to land (loose on purpose, since several mappings are
defensible). Scoring also checks structural validity for every case.

QA_CASES test the free-text career-coach mode and are graded by an LLM judge
against a rubric (see run_evals.py).
"""

ANALYZER_CASES = [
    {
        "id": "data_analyst",
        "desc": "Data Analyst at a fintech startup. You will write SQL queries against our warehouse, build dashboards in Tableau, and present weekly KPI trends to leadership. Required: strong SQL, comfort with statistics, clear written communication.",
        "expect_any": ["Mathematics", "Programming", "Computers and Electronics"],
    },
    {
        "id": "rn_nurse",
        "desc": "Registered Nurse, medical-surgical unit. Provide direct patient care, administer medications, monitor vital signs, and educate patients and families. Must hold an active RN license and show strong bedside communication and empathy.",
        "expect_any": ["Medicine and Dentistry", "Customer and Personal Service", "Therapy and Counseling"],
    },
    {
        "id": "sw_engineer",
        "desc": "Software Engineer (Backend). Design and build REST APIs in Python, debug production issues, and collaborate on system architecture. Required: 2+ years writing production code, data structures, and version control.",
        "expect_any": ["Programming", "Computers and Electronics", "Engineering and Technology"],
    },
    {
        "id": "marketing_coordinator",
        "desc": "Marketing Coordinator. Plan social campaigns, write copy for email and ads, coordinate with designers, and track engagement metrics. Strong writing and an eye for what makes people click are must-haves.",
        "expect_any": ["Sales and Marketing", "Communications and Media", "Writing"],
    },
    {
        "id": "elementary_teacher",
        "desc": "3rd Grade Teacher. Plan and deliver lessons aligned to state standards, manage a classroom of 25 students, assess progress, and communicate with parents. Requires a teaching credential and patience.",
        "expect_any": ["Education and Training", "Instructing", "Learning Strategies"],
    },
    {
        "id": "financial_analyst",
        "desc": "Financial Analyst. Build financial models in Excel, analyze quarterly performance, forecast revenue, and prepare reports for the CFO. Requires accounting fundamentals and advanced spreadsheet skills.",
        "expect_any": ["Economics and Accounting", "Mathematics", "Management of Financial Resources"],
    },
    {
        "id": "mechanical_engineer",
        "desc": "Mechanical Engineer. Design components in CAD, run stress simulations, and oversee prototyping. Required: degree in mechanical engineering, understanding of materials and manufacturing processes.",
        "expect_any": ["Engineering and Technology", "Mechanical", "Design"],
    },
    {
        "id": "sales_rep",
        "desc": "Account Executive. Own a sales pipeline, run discovery calls, negotiate contracts, and hit quarterly quota. We want a persuasive closer who listens well and follows up relentlessly.",
        "expect_any": ["Sales and Marketing", "Persuasion", "Negotiation"],
    },
    {
        "id": "hr_generalist",
        "desc": "HR Generalist. Manage recruiting, onboarding, employee relations, and benefits administration. Strong interpersonal skills and discretion required.",
        "expect_any": ["Personnel and Human Resources", "Administration and Management", "Social Perceptiveness"],
    },
    {
        "id": "graphic_designer",
        "desc": "Graphic Designer. Create brand assets, social graphics, and marketing collateral in Figma and Adobe Creative Suite. A strong portfolio and visual taste are essential.",
        "expect_any": ["Design", "Fine Arts", "Communications and Media"],
    },
    {
        "id": "ops_manager",
        "desc": "Operations Manager at a logistics company. Oversee warehouse staff, optimize shipping workflows, manage inventory, and control costs. Requires people management and process improvement experience.",
        "expect_any": ["Administration and Management", "Management of Personnel Resources", "Operations Analysis", "Transportation"],
    },
    {
        "id": "customer_support",
        "desc": "Customer Support Specialist. Answer tickets, troubleshoot product issues, and turn frustrated users into happy ones. Patience, clear writing, and genuine care for customers are key.",
        "expect_any": ["Customer and Personal Service", "Service Orientation", "Writing"],
    },
    {
        "id": "lab_technician",
        "desc": "Lab Technician. Run chemical assays, document results, calibrate instruments, and maintain quality control standards in a research lab. Background in chemistry required.",
        "expect_any": ["Chemistry", "Science", "Quality Control Analysis"],
    },
    {
        "id": "project_manager",
        "desc": "Project Manager. Coordinate cross-functional teams, manage timelines and budgets, run standups, and remove blockers. PMP a plus. Strong organization and decision-making required.",
        "expect_any": ["Administration and Management", "Coordination", "Time Management", "Judgment and Decision Making"],
    },
    {
        "id": "paralegal",
        "desc": "Paralegal. Draft legal documents, conduct case research, manage filings, and support attorneys at trial. Requires sharp reading comprehension and attention to legal detail.",
        "expect_any": ["Law and Government", "Reading Comprehension", "Writing"],
    },
    {
        "id": "it_support",
        "desc": "IT Support Technician. Set up workstations, resolve network and hardware issues, manage user accounts, and maintain documentation. CompTIA A+ preferred.",
        "expect_any": ["Computers and Electronics", "Telecommunications", "Critical Thinking"],
    },
]

QA_CASES = [
    {
        "id": "no_idea_grad",
        "question": "I just graduated with a general business degree and I have no idea what career to pursue. Where do I even start?",
        "rubric": "Gives a concrete first step the person can take this week; is encouraging and not preachy; avoids vague platitudes; ideally points to exploring skills or interests.",
    },
    {
        "id": "career_switch_ux",
        "question": "I'm a 32-year-old teacher who wants to switch into UX design. Is it too late and how would I start?",
        "rubric": "Reassures it is not too late without empty cheerleading; gives a realistic concrete path (portfolio, learning a tool, transferable skills); does not invent statistics.",
    },
    {
        "id": "data_no_experience",
        "question": "How do I get into data analysis when I have zero professional experience?",
        "rubric": "Names specific, free or low-cost ways to build a portfolio or skill; gives an actionable next step; honest about effort required; does not fabricate job-market numbers.",
    },
    {
        "id": "money_question",
        "question": "Should I cash out my 401k to pay for a coding bootcamp?",
        "rubric": "Does NOT give specific financial advice; gently suggests consulting a qualified financial professional; still offers helpful framing on the career question; stays warm.",
    },
]
