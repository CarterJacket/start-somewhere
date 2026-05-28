#!/usr/bin/env python3
"""
build_skills_v2.py — Improved pipeline that surfaces DIFFERENTIATING skills.

Key improvement: instead of just ranking by coverage%, we compute how much more
important a skill/knowledge is for THIS major/sector vs. the global average.
This prevents "Critical Thinking" from dominating everything.
"""
import json, csv, os, sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def read_tsv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)
    return rows

# ── Load O*NET data ──────────────────────────────────────────────
print("Loading O*NET data...")
skills_rows = read_tsv(os.path.join(SCRIPT_DIR, "Skills.txt"))
knowledge_rows = read_tsv(os.path.join(SCRIPT_DIR, "Knowledge.txt"))
occ_rows = read_tsv(os.path.join(SCRIPT_DIR, "Occupation Data.txt"))

print(f"  Skills rows: {len(skills_rows)}")
print(f"  Knowledge rows: {len(knowledge_rows)}")
print(f"  Occupation rows: {len(occ_rows)}")

# Build occupation title lookup
occ_titles = {}
for r in occ_rows:
    code = r.get('O*NET-SOC Code', '')
    title = r.get('Title', '')
    if code and title:
        occ_titles[code] = title

# ── Parse skills + knowledge into per-occupation profiles ────────
# Structure: occ_profiles[soc_code][skill_name] = {"im": float, "lv": float, "type": "skill"|"knowledge"}

occ_profiles = defaultdict(dict)

def parse_rows(rows, item_type):
    for r in rows:
        code = r.get('O*NET-SOC Code', '')
        name = r.get('Element Name', '')
        scale = r.get('Scale ID', '')
        suppress = r.get('Recommend Suppress', '')
        try:
            val = float(r.get('Data Value', 0))
        except:
            continue
        if not code or not name or suppress == 'Y':
            continue
        if scale == 'IM':
            if name not in occ_profiles[code]:
                occ_profiles[code][name] = {"im": 0, "lv": 0, "type": item_type}
            occ_profiles[code][name]["im"] = val
        elif scale == 'LV':
            if name not in occ_profiles[code]:
                occ_profiles[code][name] = {"im": 0, "lv": 0, "type": item_type}
            occ_profiles[code][name]["lv"] = val

parse_rows(skills_rows, "skill")
parse_rows(knowledge_rows, "knowledge")

print(f"  Occupations with profiles: {len(occ_profiles)}")

# ── Compute global averages for each skill/knowledge ─────────────
# This lets us find what's uniquely important for a group
global_sums = defaultdict(lambda: {"total_im": 0, "count": 0})
for code, profile in occ_profiles.items():
    for name, data in profile.items():
        global_sums[name]["total_im"] += data["im"]
        global_sums[name]["count"] += 1

global_avg = {}
for name, agg in global_sums.items():
    global_avg[name] = agg["total_im"] / agg["count"] if agg["count"] > 0 else 0

# ── Load mappings ────────────────────────────────────────────────
with open(os.path.join(SCRIPT_DIR, "major_occupation_map.json")) as f:
    major_map = json.load(f)
with open(os.path.join(SCRIPT_DIR, "sector_occupation_map.json")) as f:
    sector_map = json.load(f)

# ── Salary data ──────────────────────────────────────────────────
SALARY = {
    "11-1011.00":"$100K–$200K+","11-1021.00":"$80K–$160K","11-1031.00":"$75K–$140K",
    "11-2011.00":"$80K–$150K","11-2021.00":"$80K–$160K","11-2022.00":"$75K–$140K",
    "11-3011.00":"$65K–$120K","11-3012.00":"$65K–$115K","11-3013.00":"$60K–$110K",
    "11-3021.00":"$95K–$170K","11-3031.00":"$90K–$160K","11-3051.00":"$60K–$110K",
    "11-3071.00":"$65K–$120K","11-3121.00":"$75K–$130K","11-9013.00":"$55K–$95K",
    "11-9021.00":"$65K–$120K","11-9032.00":"$60K–$105K","11-9041.00":"$70K–$130K",
    "11-9051.00":"$50K–$90K","11-9081.00":"$55K–$100K","11-9111.00":"$65K–$120K",
    "11-9141.00":"$60K–$110K","11-9151.00":"$50K–$90K","11-9199.00":"$60K–$115K",
    "13-1031.00":"$50K–$90K","13-1041.00":"$55K–$95K","13-1071.00":"$55K–$100K",
    "13-1081.00":"$55K–$100K","13-1082.00":"$55K–$100K","13-1111.00":"$60K–$110K",
    "13-1121.00":"$50K–$85K","13-1131.00":"$50K–$85K","13-1151.00":"$55K–$95K",
    "13-1161.00":"$55K–$95K","13-1199.00":"$55K–$95K",
    "13-2011.00":"$60K–$110K","13-2011.01":"$60K–$110K","13-2011.02":"$60K–$110K",
    "13-2021.00":"$55K–$95K","13-2023.00":"$55K–$95K","13-2031.00":"$55K–$95K",
    "13-2041.00":"$60K–$110K","13-2051.00":"$70K–$130K","13-2052.00":"$65K–$130K",
    "13-2054.00":"$70K–$130K","13-2061.00":"$55K–$95K","13-2082.00":"$40K–$70K",
    "15-1211.00":"$70K–$120K","15-1212.00":"$60K–$100K","15-1221.00":"$75K–$130K",
    "15-1231.00":"$55K–$95K","15-1232.00":"$60K–$100K","15-1241.00":"$60K–$100K",
    "15-1243.00":"$60K–$110K","15-1244.00":"$80K–$140K","15-1245.00":"$75K–$130K",
    "15-1251.00":"$70K–$120K","15-1252.00":"$90K–$160K","15-1253.00":"$85K–$150K",
    "15-1254.00":"$90K–$150K","15-1255.00":"$60K–$110K","15-1256.00":"$85K–$140K",
    "15-1299.08":"$70K–$110K","15-1299.09":"$60K–$100K",
    "15-2021.00":"$70K–$120K","15-2031.00":"$65K–$115K","15-2041.00":"$70K–$120K",
    "15-2051.00":"$75K–$130K","15-2099.00":"$65K–$110K",
    "17-1011.00":"$60K–$110K","17-1012.00":"$55K–$90K","17-1022.00":"$55K–$90K",
    "17-2011.00":"$80K–$140K","17-2031.00":"$70K–$120K","17-2041.00":"$75K–$130K",
    "17-2051.00":"$65K–$115K","17-2061.00":"$75K–$130K","17-2071.00":"$70K–$120K",
    "17-2072.00":"$70K–$120K","17-2081.00":"$65K–$115K","17-2112.00":"$70K–$120K",
    "17-2121.00":"$65K–$110K","17-2131.00":"$65K–$115K","17-2141.00":"$65K–$115K",
    "17-2151.00":"$75K–$125K","17-2161.00":"$65K–$115K","17-2171.00":"$65K–$120K",
    "17-2199.00":"$65K–$115K","17-3011.00":"$45K–$75K","17-3013.00":"$45K–$75K",
    "17-3023.00":"$45K–$75K","17-3026.00":"$50K–$80K","17-3027.00":"$45K–$75K",
    "19-1011.00":"$55K–$95K","19-1012.00":"$50K–$85K","19-1013.00":"$50K–$85K",
    "19-1021.00":"$60K–$100K","19-1022.00":"$55K–$95K","19-1023.00":"$55K–$90K",
    "19-1029.00":"$55K–$90K","19-1031.00":"$55K–$95K","19-1032.00":"$50K–$85K",
    "19-1041.00":"$55K–$95K","19-1042.00":"$55K–$90K",
    "19-2012.00":"$60K–$100K","19-2021.00":"$55K–$95K","19-2031.00":"$60K–$100K",
    "19-2032.00":"$55K–$95K","19-2041.00":"$55K–$90K","19-2042.00":"$60K–$100K",
    "19-2043.00":"$55K–$95K","19-2099.00":"$55K–$90K",
    "19-3011.00":"$70K–$120K","19-3022.00":"$55K–$90K","19-3032.00":"$55K–$90K",
    "19-3034.00":"$50K–$85K","19-3041.00":"$55K–$90K","19-3051.00":"$50K–$85K",
    "19-3094.00":"$55K–$90K","19-4042.00":"$40K–$65K","19-4061.00":"$40K–$65K",
    "21-1011.00":"$40K–$70K","21-1012.00":"$45K–$70K","21-1013.00":"$40K–$60K",
    "21-1014.00":"$35K–$55K","21-1015.00":"$35K–$55K","21-1018.00":"$40K–$65K",
    "21-1019.00":"$35K–$60K","21-1021.00":"$35K–$55K","21-1022.00":"$40K–$65K",
    "21-1023.00":"$35K–$55K","21-1091.00":"$45K–$75K","21-1092.00":"$40K–$65K",
    "21-1093.00":"$40K–$65K","21-2011.00":"$35K–$60K","21-2021.00":"$35K–$55K",
    "23-1011.00":"$80K–$180K","23-1012.00":"$70K–$120K","23-1021.00":"$65K–$120K",
    "23-1022.00":"$65K–$120K","23-1023.00":"$60K–$110K","23-2011.00":"$45K–$80K",
    "23-2093.00":"$45K–$75K","23-2099.00":"$45K–$75K",
    "25-1011.00":"$55K–$100K","25-1021.00":"$50K–$90K","25-1022.00":"$50K–$90K",
    "25-1031.00":"$50K–$90K","25-1032.00":"$50K–$90K","25-1042.00":"$55K–$100K",
    "25-1043.00":"$55K–$100K","25-1051.00":"$55K–$100K","25-1052.00":"$55K–$100K",
    "25-1053.00":"$55K–$100K","25-1054.00":"$55K–$100K","25-1065.00":"$55K–$100K",
    "25-1066.00":"$55K–$100K","25-1067.00":"$55K–$100K","25-1069.00":"$55K–$100K",
    "25-1071.00":"$55K–$95K","25-1081.00":"$50K–$90K","25-1082.00":"$50K–$90K",
    "25-1112.00":"$55K–$100K","25-1113.00":"$55K–$100K","25-1121.00":"$55K–$100K",
    "25-1122.00":"$55K–$100K","25-1124.00":"$55K–$100K","25-1125.00":"$55K–$100K",
    "25-1126.00":"$55K–$100K","25-2011.00":"$40K–$65K","25-2012.00":"$40K–$65K",
    "25-2021.00":"$45K–$70K","25-2022.00":"$45K–$70K","25-2031.00":"$50K–$75K",
    "25-2032.00":"$45K–$70K","25-2054.00":"$50K–$80K","25-2058.00":"$50K–$75K",
    "25-2059.00":"$45K–$70K","25-3021.00":"$40K–$65K","25-3031.00":"$40K–$65K",
    "25-9031.00":"$45K–$70K","25-9042.00":"$40K–$65K","25-9045.00":"$45K–$75K",
    "27-1011.00":"$40K–$80K","27-1013.00":"$40K–$80K","27-1014.00":"$45K–$85K",
    "27-1021.00":"$55K–$100K","27-1022.00":"$55K–$100K","27-1024.00":"$50K–$90K",
    "27-1025.00":"$45K–$80K","27-1027.00":"$45K–$80K",
    "27-2011.00":"$40K–$100K","27-2012.00":"$45K–$100K","27-2041.00":"$50K–$90K",
    "27-2042.00":"$45K–$80K","27-3011.00":"$50K–$90K","27-3023.00":"$35K–$70K",
    "27-3031.00":"$50K–$90K","27-3041.00":"$45K–$80K","27-3042.00":"$50K–$90K",
    "27-3043.00":"$45K–$85K","27-3091.00":"$50K–$90K","27-3092.00":"$45K–$80K",
    "27-4011.00":"$40K–$75K","27-4021.00":"$45K–$80K","27-4031.00":"$40K–$75K",
    "29-1011.00":"$55K–$85K","29-1021.00":"$55K–$80K","29-1031.00":"$55K–$85K",
    "29-1041.00":"$60K–$105K","29-1051.00":"$70K–$115K","29-1071.00":"$85K–$130K",
    "29-1122.00":"$60K–$95K","29-1123.00":"$60K–$95K","29-1124.00":"$55K–$90K",
    "29-1125.00":"$55K–$90K","29-1126.00":"$50K–$85K","29-1127.00":"$55K–$95K",
    "29-1128.00":"$60K–$100K","29-1131.00":"$55K–$90K","29-1141.00":"$60K–$105K",
    "29-1151.00":"$70K–$95K","29-1161.00":"$85K–$130K","29-1171.00":"$85K–$130K",
    "29-1211.00":"$175K–$350K+","29-1212.00":"$60K–$95K","29-1213.00":"$70K–$110K",
    "29-1214.00":"$175K–$350K+","29-1215.00":"$175K–$350K+","29-1216.00":"$175K–$350K+",
    "29-1217.00":"$175K–$350K+","29-1218.00":"$175K–$350K+","29-1221.00":"$70K–$110K",
    "29-1222.00":"$175K–$350K+","29-1223.00":"$175K–$350K+","29-1224.00":"$175K–$350K+",
    "29-1228.00":"$175K–$350K+","29-1229.00":"$175K–$350K+","29-1241.00":"$60K–$100K",
    "29-1242.00":"$55K–$80K","29-1243.00":"$55K–$80K","29-1248.00":"$55K–$80K",
    "29-1249.00":"$55K–$80K","29-1291.00":"$55K–$85K","29-1292.00":"$55K–$85K",
    "29-1299.00":"$55K–$85K","29-2011.00":"$40K–$65K","29-2012.00":"$45K–$75K",
    "29-2018.00":"$40K–$65K","29-2032.00":"$40K–$65K","29-2033.00":"$40K–$65K",
    "29-2034.00":"$40K–$65K","29-2036.00":"$45K–$70K","29-2042.00":"$35K–$55K",
    "29-2052.00":"$35K–$55K","29-2053.00":"$30K–$50K","29-2056.00":"$50K–$85K",
    "29-2061.00":"$45K–$75K","29-2081.00":"$45K–$75K","29-2091.00":"$55K–$90K",
    "29-2099.00":"$40K–$65K","29-9011.00":"$45K–$80K","29-9021.00":"$40K–$65K",
    "29-9091.00":"$40K–$65K","29-9092.00":"$55K–$90K",
    "31-1120.00":"$25K–$40K","31-1131.00":"$25K–$40K","31-1133.00":"$30K–$45K",
    "31-2011.00":"$30K–$50K","31-2012.00":"$30K–$50K","31-2021.00":"$35K–$55K",
    "31-9011.00":"$30K–$45K","31-9091.00":"$35K–$55K","31-9092.00":"$30K–$50K",
    "31-9097.00":"$30K–$45K",
    "33-1011.00":"$50K–$90K","33-1012.00":"$65K–$110K","33-1021.00":"$55K–$90K",
    "33-2011.00":"$40K–$70K","33-3011.00":"$40K–$70K","33-3012.00":"$45K–$75K",
    "33-3021.00":"$45K–$80K","33-3031.00":"$50K–$85K","33-3051.00":"$50K–$85K",
    "33-3052.00":"$45K–$75K","33-9032.00":"$35K–$55K",
    "37-1012.00":"$35K–$55K","39-1014.00":"$30K–$50K","39-3031.00":"$35K–$60K",
    "39-5012.00":"$25K–$45K","39-9032.00":"$30K–$50K",
    "41-1012.00":"$45K–$80K","41-2031.00":"$25K–$50K","41-3011.00":"$45K–$85K",
    "41-3031.00":"$50K–$95K","41-3091.00":"$55K–$105K","41-4011.00":"$55K–$100K",
    "41-4012.00":"$55K–$100K","41-9021.00":"$50K–$90K","41-9022.00":"$50K–$90K",
    "41-9031.00":"$45K–$85K","41-9099.00":"$40K–$75K",
    "43-1011.00":"$40K–$65K","43-3031.00":"$35K–$55K","43-4051.00":"$35K–$55K",
    "43-4061.00":"$30K–$50K","43-4171.00":"$35K–$55K","43-6011.00":"$35K–$60K",
    "43-6014.00":"$30K–$50K","43-9061.00":"$35K–$55K",
    "45-1011.00":"$35K–$60K","45-2011.00":"$30K–$50K","45-2021.00":"$30K–$50K",
    "45-2092.00":"$30K–$55K","45-2093.00":"$30K–$50K",
    "47-1011.00":"$50K–$85K","47-2031.00":"$40K–$70K","47-2061.00":"$40K–$65K",
    "47-2073.00":"$40K–$70K","47-2111.00":"$45K–$75K","47-2152.00":"$40K–$65K",
    "47-4011.00":"$45K–$75K","47-4099.00":"$40K–$65K",
    "49-1011.00":"$50K–$85K","49-2011.00":"$45K–$75K","49-2094.00":"$45K–$75K",
    "49-2095.00":"$40K–$70K","49-3011.00":"$40K–$65K","49-3023.00":"$40K–$65K",
    "49-3042.00":"$40K–$65K","49-9012.00":"$45K–$75K","49-9021.00":"$45K–$70K",
    "49-9041.00":"$45K–$75K","49-9051.00":"$45K–$75K","49-9071.00":"$45K–$70K",
    "51-1011.00":"$45K–$75K","51-2041.00":"$35K–$55K","51-4041.00":"$40K–$65K",
    "51-8013.00":"$50K–$85K","51-8031.00":"$45K–$75K","51-9061.00":"$35K–$55K",
    "53-1042.00":"$45K–$75K","53-1043.00":"$45K–$80K","53-1044.00":"$50K–$85K",
    "53-1047.00":"$45K–$80K","53-1048.00":"$45K–$75K","53-2011.00":"$70K–$130K",
    "53-2012.00":"$55K–$100K","53-5021.00":"$50K–$90K","53-6051.00":"$40K–$65K",
}

# ── Practical skill descriptions keyed by O*NET name ─────────────
SKILL_DESC = {
    # Knowledge areas (these are the differentiators)
    "Computers and Electronics": "Software, hardware, programming, and systems design",
    "Engineering and Technology": "Applying engineering principles to design and build solutions",
    "Mathematics": "Arithmetic, algebra, geometry, calculus, statistics, and their applications",
    "Economics and Accounting": "Financial principles, markets, banking, and cost analysis",
    "Administration and Management": "Business strategy, planning, resource allocation, and leadership",
    "Sales and Marketing": "Product promotion, sales strategy, and consumer behavior",
    "Customer and Personal Service": "Meeting client needs, quality standards, and satisfaction",
    "Personnel and Human Resources": "Recruiting, hiring, training, compensation, and labor relations",
    "English Language": "Grammar, composition, and language structure for communication",
    "Education and Training": "Curriculum design, teaching methods, and learning assessment",
    "Psychology": "Human behavior, motivation, mental processes, and individual differences",
    "Sociology and Anthropology": "Group behavior, social structures, and cultural dynamics",
    "Law and Government": "Laws, regulations, court procedures, and government processes",
    "Public Safety and Security": "Safety protocols, rules, regulations, and emergency procedures",
    "Communications and Media": "Media production, communication methods, and dissemination techniques",
    "Chemistry": "Substances, reactions, chemical processes, and laboratory techniques",
    "Biology": "Plant/animal organisms, cells, genetics, and ecosystems",
    "Physics": "Physical principles, laws, applications, and mechanics",
    "Medicine and Dentistry": "Diagnosing and treating injuries, diseases, and disorders",
    "Therapy and Counseling": "Treatment methods, rehabilitation, and career guidance",
    "Geography": "Land features, climate, population distribution, and spatial analysis",
    "History and Archeology": "Historical events, cultures, and their causes and indicators",
    "Philosophy and Theology": "Ethical principles, religions, and philosophical systems",
    "Telecommunications": "Transmission systems, broadcasting, and communication technologies",
    "Transportation": "Moving people or goods by road, rail, air, or water",
    "Production and Processing": "Manufacturing inputs, outputs, quality control, and costs",
    "Food Production": "Growing, harvesting, and processing food products",
    "Building and Construction": "Materials, methods, and tools for construction projects",
    "Mechanical": "Machines, tools, design, use, repair, and maintenance",
    "Design": "Design techniques, tools, and principles for plans and drawings",
    "Fine Arts": "Theory and techniques for music, dance, visual arts, and drama",
    "Clerical": "Office procedures, word processing, records management, and filing",
    "Foreign Language": "Structure and content of foreign languages",
    # Essential/Transferable Skills (only the differentiating ones)
    "Programming": "Writing code, debugging, and building software applications",
    "Operations Analysis": "Analyzing business needs and designing systems and processes",
    "Technology Design": "Designing or adapting technology solutions for specific needs",
    "Systems Analysis": "Determining how a system should work and how changes affect outcomes",
    "Systems Evaluation": "Identifying system performance measures and improvement actions",
    "Quality Control Analysis": "Conducting tests and inspections to ensure quality standards",
    "Science": "Using scientific rules and methods to solve problems",
    "Complex Problem Solving": "Identifying tough problems and developing creative solutions",
    "Operations Monitoring": "Watching gauges, dials, and outputs to ensure proper operation",
    "Equipment Selection": "Choosing the right tools and equipment for a job",
    "Equipment Maintenance": "Performing routine maintenance and determining servicing needs",
    "Installation": "Installing equipment, machines, wiring, or programs to specification",
    "Repairing": "Fixing machines or systems using the right tools",
    "Troubleshooting": "Determining causes of operating errors and deciding how to fix them",
    "Operation and Control": "Controlling operations of equipment or systems",
    "Negotiation": "Bringing others together and trying to reconcile differences",
    "Persuasion": "Convincing others to change their minds or behavior",
    "Instructing": "Teaching others how to do something",
    "Service Orientation": "Actively looking for ways to help people",
    "Social Perceptiveness": "Being aware of others' reactions and understanding why they react",
    "Coordination": "Adjusting actions in relation to others' actions",
    "Time Management": "Managing one's own time and the time of others",
    "Management of Personnel Resources": "Motivating, developing, and directing people as they work",
    "Management of Financial Resources": "Determining how money will be spent and accounting for it",
    "Management of Material Resources": "Obtaining and managing the appropriate use of resources",
    "Reading Comprehension": "Understanding written documents, reports, and procedures",
    "Active Listening": "Fully concentrating on what others say to understand their needs",
    "Writing": "Communicating effectively through written documents and reports",
    "Speaking": "Talking to others clearly and effectively to convey information",
    "Critical Thinking": "Using logic and reasoning to evaluate options and decisions",
    "Active Learning": "Understanding new information for current and future problem-solving",
    "Learning Strategies": "Selecting and using training methods appropriate for the situation",
    "Monitoring": "Assessing performance of yourself, others, or organizations",
    "Judgment and Decision Making": "Weighing costs, benefits, and risks to make smart calls",
}

# Skills that are near-universal (global avg importance > 3.2). These are only shown
# if they score significantly higher for this specific group (diff > 0.5)
UNIVERSAL_SKILLS = {
    "Reading Comprehension", "Active Listening", "Speaking", "Critical Thinking",
    "Writing", "Monitoring", "Active Learning", "Coordination",
    "Time Management", "Social Perceptiveness", "Judgment and Decision Making",
    "English Language", "Service Orientation", "Customer and Personal Service",
    "Complex Problem Solving",
}

# ── Compute skills for a group of occupations ────────────────────
def compute_group_skills(occ_codes, n_skills=10):
    """Returns top skills ranked by differentiation score."""
    # Find which codes exist in our data
    matched = [c for c in occ_codes if c in occ_profiles]
    if not matched:
        return [], 0

    total = len(matched)

    # Aggregate: for each skill, count occupations where importance >= 3.5
    # and compute average importance
    skill_stats = defaultdict(lambda: {"count_high": 0, "sum_im": 0, "n": 0, "type": ""})
    for code in matched:
        for name, data in occ_profiles[code].items():
            skill_stats[name]["sum_im"] += data["im"]
            skill_stats[name]["n"] += 1
            skill_stats[name]["type"] = data["type"]
            if data["im"] >= 4.0:
                skill_stats[name]["count_high"] += 1

    # Score each skill:
    # coverage = count_high / total
    # avg_importance = sum_im / n
    # differentiation = avg_importance - global_average
    # final_score = coverage * (1 + differentiation)
    # This rewards skills that are both common AND uniquely important
    scored = []
    for name, stats in skill_stats.items():
        if stats["n"] < max(1, total * 0.3):  # Must appear in at least 30% of occupations
            continue
        coverage = stats["count_high"] / total
        avg_im = stats["sum_im"] / stats["n"]
        g_avg = global_avg.get(name, 0)
        diff = avg_im - g_avg

        # Knowledge areas get a bonus since they're more specific/actionable
        type_bonus = 1.5 if stats["type"] == "knowledge" else 1.0

        # Universal skills only appear if truly differentiated for this group
        if name in UNIVERSAL_SKILLS:
            if diff < 0.5:
                type_bonus *= 0.05  # Nearly eliminate universal skills unless very differentiated
            else:
                type_bonus *= 0.5  # Still penalize but allow through

        score = coverage * (1 + max(0, diff)) * type_bonus
        pct = round(coverage * 100)

        scored.append({
            "name": name,
            "pct": pct,
            "score": score,
            "avg_im": avg_im,
            "diff": diff,
            "type": stats["type"],
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Pick top N, assign colors
    colors = ["var(--accent)"] * 3 + ["var(--teal)"] * 2 + ["var(--blue)"] * 2 + ["var(--purple)"] * 10
    result = []
    for i, s in enumerate(scored[:n_skills]):
        desc = SKILL_DESC.get(s["name"], f"Core competency in {s['name'].lower()}")
        result.append({
            "name": s["name"],
            "desc": desc,
            "pct": s["pct"],
            "color": colors[min(i, len(colors) - 1)],
        })

    # Compute hedge: top 3 skills union coverage
    if len(scored) >= 3:
        top3_names = [s["name"] for s in scored[:3]]
        covered_occs = set()
        for code in matched:
            for name in top3_names:
                if name in occ_profiles[code] and occ_profiles[code][name]["im"] >= 4.0:
                    covered_occs.add(code)
                    break
        hedge = round(len(covered_occs) / total * 100)
    else:
        hedge = 0

    return result, hedge

# ── Generate insight text ────────────────────────────────────────
def make_insight(name, skills, hedge, is_sector=False):
    if len(skills) < 3:
        return f"Build skills in this area to stand out."
    top3 = " + ".join(s["name"] for s in skills[:3])
    context = "sector" if is_sector else "field"
    if hedge >= 85:
        return f"<strong>{top3}</strong> cover {hedge}% of career paths in this {context}. Master these three and you're competitive nearly everywhere — then specialize based on what excites you most."
    elif hedge >= 70:
        return f"<strong>{top3}</strong> cover {hedge}% of roles in this {context}. That's strong foundational coverage. Adding {skills[3]['name'] if len(skills) > 3 else 'one more specialized skill'} pushes you into even more territory."
    else:
        return f"This {context} rewards specialization. <strong>{top3}</strong> get you to {hedge}% coverage, but the remaining roles require more targeted skills. Pick a lane early and go deep."

# ── Build output ─────────────────────────────────────────────────
print("\nProcessing majors...")
output = {"majors": {}, "sectors": {}}

for major_name, major_data in major_map.items():
    occs = major_data.get("occupations", [])
    category = major_data.get("category", "Other")
    matched = [c for c in occs if c in occ_profiles]

    skills, hedge = compute_group_skills(occs)

    # Build career list from occupation titles
    careers = []
    for code in matched:
        if code in occ_titles:
            careers.append({
                "title": occ_titles[code],
                "salary": SALARY.get(code, "$50K–$90K")
            })
    # Deduplicate by title
    seen_titles = set()
    unique_careers = []
    for c in careers:
        if c["title"] not in seen_titles:
            seen_titles.add(c["title"])
            unique_careers.append(c)

    hedge_color = "var(--teal)" if hedge >= 75 else ("var(--accent)" if hedge >= 60 else "var(--purple)")
    insight = make_insight(major_name, skills, hedge)

    output["majors"][major_name] = {
        "category": category,
        "skills": skills,
        "careers": unique_careers[:12],
        "hedgePct": hedge,
        "hedgeColor": hedge_color,
        "insight": insight,
    }
    print(f"  {major_name}: {len(matched)}/{len(occs)} matched, {len(skills)} skills, hedge={hedge}%")

print("\nProcessing sectors...")
for sector_name, sector_data in sector_map.items():
    occs = sector_data.get("occupations", [])
    matched = [c for c in occs if c in occ_profiles]

    skills, hedge = compute_group_skills(occs)

    careers = []
    for code in matched:
        if code in occ_titles:
            careers.append({
                "title": occ_titles[code],
                "salary": SALARY.get(code, "$50K–$90K")
            })
    seen_titles = set()
    unique_careers = []
    for c in careers:
        if c["title"] not in seen_titles:
            seen_titles.add(c["title"])
            unique_careers.append(c)

    hedge_color = "var(--teal)" if hedge >= 75 else ("var(--accent)" if hedge >= 60 else "var(--purple)")
    insight = make_insight(sector_name, skills, hedge, is_sector=True)

    output["sectors"][sector_name] = {
        "skills": skills,
        "careers": unique_careers[:12],
        "hedgePct": hedge,
        "hedgeColor": hedge_color,
        "insight": insight,
    }
    print(f"  {sector_name}: {len(matched)}/{len(occs)} matched, {len(skills)} skills, hedge={hedge}%")

# Write output
out_path = os.path.join(os.path.dirname(SCRIPT_DIR), "skills_explorer_data.json")
with open(out_path, 'w') as f:
    json.dump(output, f, indent=2)
print(f"\nOutput: {out_path} ({os.path.getsize(out_path):,} bytes)")
print(f"Majors: {len(output['majors'])}, Sectors: {len(output['sectors'])}")
