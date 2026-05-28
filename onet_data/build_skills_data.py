#!/usr/bin/env python3
"""
build_skills_data.py

Reads O*NET tab-separated text files and the two JSON mapping files to produce
a single skills_explorer_data.json consumed by the Start Somewhere frontend.

Expected O*NET files in the same directory as this script:
  - Skills.txt
  - Knowledge.txt
  - Occupation Data.txt

Mapping files (same directory):
  - major_occupation_map.json
  - sector_occupation_map.json

Output:
  - ../skills_explorer_data.json  (one level up from onet_data/)
"""

import json
import csv
import os
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "skills_explorer_data.json")

MAJOR_MAP_PATH = os.path.join(SCRIPT_DIR, "major_occupation_map.json")
SECTOR_MAP_PATH = os.path.join(SCRIPT_DIR, "sector_occupation_map.json")

SKILLS_FILE = os.path.join(SCRIPT_DIR, "Skills.txt")
KNOWLEDGE_FILE = os.path.join(SCRIPT_DIR, "Knowledge.txt")
OCCUPATION_FILE = os.path.join(SCRIPT_DIR, "Occupation Data.txt")

# ---------------------------------------------------------------------------
# Salary data (BLS median ranges, from training knowledge)
# ---------------------------------------------------------------------------
SALARY_MAP = {
    # Management
    "11-1011.00": "$100K-$200K+", "11-1021.00": "$80K-$160K", "11-1031.00": "$75K-$140K",
    "11-2011.00": "$80K-$150K", "11-2021.00": "$80K-$160K", "11-2022.00": "$75K-$140K",
    "11-3011.00": "$65K-$120K", "11-3012.00": "$65K-$115K", "11-3013.00": "$60K-$110K",
    "11-3021.00": "$95K-$170K", "11-3031.00": "$90K-$160K", "11-3051.00": "$60K-$110K",
    "11-3071.00": "$65K-$120K", "11-3071.01": "$65K-$120K", "11-3071.04": "$65K-$120K",
    "11-3121.00": "$75K-$130K", "11-9013.00": "$55K-$95K", "11-9021.00": "$65K-$120K",
    "11-9032.00": "$60K-$105K", "11-9041.00": "$70K-$130K", "11-9051.00": "$50K-$90K",
    "11-9081.00": "$55K-$100K", "11-9111.00": "$65K-$120K", "11-9111.01": "$65K-$120K",
    "11-9141.00": "$60K-$110K", "11-9151.00": "$50K-$90K", "11-9199.00": "$60K-$115K",
    # Business / Financial
    "13-1031.00": "$50K-$90K", "13-1041.00": "$55K-$95K", "13-1071.00": "$55K-$100K",
    "13-1081.00": "$55K-$100K", "13-1082.00": "$55K-$100K", "13-1111.00": "$60K-$110K",
    "13-1121.00": "$50K-$85K", "13-1131.00": "$50K-$85K", "13-1161.00": "$55K-$95K",
    "13-1161.01": "$55K-$95K", "13-1199.00": "$55K-$95K",
    "13-2011.00": "$60K-$110K", "13-2011.01": "$60K-$110K", "13-2011.02": "$60K-$110K",
    "13-2021.00": "$55K-$95K", "13-2023.00": "$55K-$95K",
    "13-2031.00": "$55K-$95K", "13-2041.00": "$60K-$110K", "13-2051.00": "$70K-$130K",
    "13-2052.00": "$65K-$130K", "13-2054.00": "$70K-$130K", "13-2061.00": "$55K-$95K",
    "13-2082.00": "$40K-$70K", "13-2099.00": "$55K-$100K",
    # Computer / Math
    "15-1211.00": "$70K-$120K", "15-1212.00": "$60K-$100K", "15-1221.00": "$75K-$130K",
    "15-1231.00": "$55K-$95K", "15-1232.00": "$60K-$100K",
    "15-1243.00": "$60K-$110K", "15-1244.00": "$80K-$140K", "15-1245.00": "$75K-$130K",
    "15-1251.00": "$70K-$120K", "15-1252.00": "$90K-$160K", "15-1253.00": "$85K-$150K",
    "15-1254.00": "$90K-$150K", "15-1255.00": "$60K-$110K", "15-1256.00": "$85K-$140K",
    "15-1299.08": "$70K-$110K", "15-1299.09": "$60K-$100K",
    "15-2021.00": "$70K-$120K", "15-2031.00": "$65K-$115K", "15-2041.00": "$70K-$120K",
    "15-2041.01": "$70K-$120K", "15-2051.00": "$75K-$130K", "15-2051.01": "$75K-$130K",
    "15-2099.00": "$65K-$110K",
    # Engineering
    "17-1011.00": "$60K-$110K", "17-1012.00": "$55K-$90K", "17-1022.00": "$55K-$90K",
    "17-2011.00": "$80K-$140K", "17-2031.00": "$70K-$120K",
    "17-2041.00": "$75K-$130K", "17-2041.01": "$75K-$130K",
    "17-2051.00": "$65K-$115K", "17-2051.01": "$65K-$115K", "17-2051.02": "$65K-$115K",
    "17-2061.00": "$75K-$130K", "17-2071.00": "$70K-$120K", "17-2072.00": "$70K-$120K",
    "17-2072.01": "$70K-$120K", "17-2081.00": "$65K-$115K", "17-2112.00": "$70K-$120K",
    "17-2141.00": "$70K-$120K", "17-2141.01": "$70K-$120K", "17-2141.02": "$70K-$120K",
    "17-2199.00": "$70K-$120K",
    "17-3011.00": "$45K-$75K", "17-3021.00": "$50K-$80K", "17-3022.00": "$45K-$75K",
    "17-3023.00": "$50K-$80K", "17-3024.00": "$50K-$80K", "17-3026.00": "$50K-$80K",
    "17-3027.00": "$50K-$80K", "17-3029.00": "$50K-$80K",
    # Life / Physical / Social Science
    "19-1011.00": "$55K-$95K", "19-1012.00": "$50K-$90K", "19-1013.00": "$55K-$95K",
    "19-1021.00": "$55K-$100K", "19-1022.00": "$55K-$95K", "19-1023.00": "$55K-$100K",
    "19-1029.00": "$55K-$95K", "19-1031.00": "$55K-$95K",
    "19-1041.00": "$55K-$100K", "19-1042.00": "$60K-$110K",
    "19-2012.00": "$70K-$130K", "19-2031.00": "$60K-$110K", "19-2032.00": "$60K-$110K",
    "19-2041.00": "$55K-$100K", "19-2041.01": "$55K-$100K", "19-2041.02": "$55K-$100K",
    "19-2041.03": "$55K-$100K", "19-2043.00": "$55K-$95K", "19-2099.00": "$60K-$110K",
    "19-3011.00": "$70K-$130K", "19-3011.01": "$70K-$130K",
    "19-3031.00": "$60K-$110K", "19-3032.00": "$65K-$120K", "19-3033.00": "$55K-$95K",
    "19-3034.00": "$55K-$95K", "19-3039.00": "$55K-$95K",
    "19-3041.00": "$55K-$95K", "19-3051.00": "$50K-$90K",
    "19-3091.00": "$50K-$85K", "19-3093.00": "$50K-$85K", "19-3094.00": "$55K-$100K",
    "19-4012.00": "$40K-$70K", "19-4021.00": "$40K-$65K", "19-4031.00": "$40K-$65K",
    "19-4042.00": "$40K-$70K", "19-4051.00": "$40K-$65K", "19-4061.00": "$40K-$70K",
    "19-4099.00": "$40K-$65K",
    # Community / Social Service
    "21-1011.00": "$40K-$65K", "21-1012.00": "$45K-$70K", "21-1013.00": "$40K-$65K",
    "21-1014.00": "$45K-$75K", "21-1015.00": "$45K-$70K", "21-1021.00": "$40K-$65K",
    "21-1022.00": "$45K-$70K", "21-1023.00": "$45K-$70K", "21-1029.00": "$40K-$65K",
    "21-1091.00": "$40K-$65K", "21-1092.00": "$40K-$65K", "21-1093.00": "$40K-$65K",
    "21-1094.00": "$45K-$70K", "21-1099.00": "$40K-$65K", "21-2011.00": "$40K-$65K",
    # Legal
    "23-1011.00": "$80K-$180K", "23-1012.00": "$80K-$150K",
    "23-1021.00": "$90K-$170K", "23-1022.00": "$80K-$160K", "23-1023.00": "$75K-$140K",
    "23-2011.00": "$45K-$75K", "23-2093.00": "$45K-$75K", "23-2099.00": "$45K-$70K",
    # Education
    "25-1011.00": "$55K-$100K", "25-1022.00": "$60K-$105K", "25-1041.00": "$60K-$100K",
    "25-1042.00": "$60K-$100K", "25-1051.00": "$65K-$110K", "25-1052.00": "$60K-$105K",
    "25-1061.00": "$55K-$90K", "25-1063.00": "$60K-$105K", "25-1065.00": "$55K-$95K",
    "25-1066.00": "$55K-$95K", "25-1067.00": "$55K-$95K",
    "25-1121.00": "$50K-$85K", "25-1123.00": "$50K-$85K", "25-1125.00": "$55K-$90K",
    "25-1126.00": "$55K-$90K", "25-1193.00": "$55K-$90K", "25-1194.00": "$55K-$90K",
    "25-1199.00": "$50K-$85K",
    "25-2011.00": "$45K-$70K", "25-2012.00": "$45K-$70K", "25-2021.00": "$45K-$70K",
    "25-2022.00": "$50K-$75K", "25-2031.00": "$50K-$80K", "25-2032.00": "$50K-$80K",
    "25-2056.00": "$50K-$75K", "25-2057.00": "$50K-$75K", "25-2058.00": "$50K-$75K",
    "25-2059.00": "$50K-$75K",
    "25-3031.00": "$35K-$55K", "25-4012.00": "$40K-$65K", "25-4013.00": "$40K-$65K",
    "25-9031.00": "$40K-$60K", "25-9041.00": "$35K-$55K",
    # Arts / Design / Entertainment
    "27-1011.00": "$40K-$80K", "27-1012.00": "$35K-$70K", "27-1013.00": "$40K-$75K",
    "27-1014.00": "$50K-$100K", "27-1019.00": "$40K-$75K", "27-1021.00": "$50K-$90K",
    "27-1024.00": "$45K-$85K", "27-1025.00": "$50K-$90K", "27-1029.00": "$45K-$80K",
    "27-2011.00": "$50K-$100K", "27-2012.00": "$50K-$100K",
    "27-2041.00": "$45K-$90K", "27-2042.00": "$45K-$85K",
    "27-3022.00": "$45K-$80K", "27-3023.00": "$45K-$80K",
    "27-3031.00": "$55K-$100K", "27-3041.00": "$50K-$90K", "27-3042.00": "$50K-$85K",
    "27-3043.00": "$50K-$90K", "27-3091.00": "$45K-$80K",
    "27-4011.00": "$40K-$70K", "27-4031.00": "$45K-$80K", "27-4032.00": "$40K-$70K",
    # Healthcare Practitioners
    "29-1011.00": "$45K-$80K", "29-1031.00": "$50K-$80K", "29-1031.01": "$50K-$80K",
    "29-1051.00": "$100K-$160K", "29-1071.00": "$80K-$130K",
    "29-1122.00": "$65K-$110K", "29-1123.00": "$60K-$100K", "29-1128.00": "$60K-$100K",
    "29-1141.00": "$60K-$100K", "29-1141.01": "$60K-$100K", "29-1141.02": "$60K-$100K",
    "29-1141.03": "$80K-$120K", "29-1151.00": "$100K-$140K", "29-1161.00": "$80K-$130K",
    "29-1171.00": "$100K-$140K",
    "29-1211.00": "$100K-$250K+", "29-1215.00": "$90K-$200K+",
    "29-1216.00": "$100K-$250K+", "29-1218.00": "$100K-$250K+",
    "29-1221.00": "$80K-$150K", "29-1223.00": "$90K-$200K+",
    "29-1228.00": "$100K-$250K+", "29-1229.00": "$100K-$200K+", "29-1241.00": "$90K-$180K",
    "29-2032.00": "$45K-$75K", "29-2052.00": "$35K-$50K", "29-2053.00": "$35K-$50K",
    "29-2061.00": "$45K-$75K", "29-2071.00": "$40K-$60K",
    "29-9021.00": "$50K-$85K", "29-9091.00": "$40K-$65K",
    # Healthcare Support
    "31-1131.00": "$30K-$45K",
    # Protective Service
    "33-1012.00": "$55K-$90K", "33-3012.00": "$50K-$85K", "33-3021.00": "$50K-$85K",
    "33-3051.00": "$50K-$85K", "33-9021.00": "$40K-$60K", "33-9032.00": "$35K-$55K",
    # Sales
    "41-1012.00": "$50K-$90K", "41-2011.00": "$30K-$50K", "41-2031.00": "$25K-$40K",
    "41-3031.00": "$55K-$100K", "41-3041.00": "$35K-$60K", "41-3091.00": "$50K-$90K",
    "41-4012.00": "$50K-$95K", "41-9021.00": "$40K-$70K", "41-9022.00": "$40K-$70K",
    "41-9099.00": "$30K-$55K",
    # Office / Admin
    "43-1011.00": "$45K-$70K", "43-3011.00": "$35K-$55K", "43-3031.00": "$35K-$55K",
    "43-3071.00": "$35K-$55K", "43-4031.00": "$35K-$55K",
    "43-5061.00": "$35K-$55K", "43-5071.00": "$35K-$55K",
    "43-6012.00": "$40K-$60K", "43-6013.00": "$35K-$55K", "43-9081.00": "$35K-$55K",
    # Construction
    "47-1011.00": "$50K-$85K", "47-2031.00": "$40K-$65K", "47-2061.00": "$40K-$70K",
    "47-2111.00": "$40K-$65K", "47-4011.00": "$45K-$75K", "47-5013.00": "$50K-$80K",
    # Installation / Maintenance
    "49-2091.00": "$50K-$80K", "49-9071.00": "$45K-$75K",
    # Production
    "51-1011.00": "$45K-$75K", "51-8013.00": "$55K-$90K", "51-9061.00": "$40K-$65K",
    # Transportation
    "53-1042.00": "$50K-$80K", "53-1043.00": "$50K-$80K",
    "53-3032.00": "$40K-$65K", "53-6051.00": "$45K-$70K",
    # Farming
    "45-1011.00": "$35K-$65K",
    # Other
    "39-1014.00": "$35K-$55K", "39-7011.00": "$35K-$55K", "39-9031.00": "$35K-$60K",
    "35-1011.00": "$35K-$55K", "35-1012.00": "$45K-$70K", "35-2014.00": "$40K-$65K",
}

# ---------------------------------------------------------------------------
# Skill description templates (field-context aware)
# ---------------------------------------------------------------------------
SKILL_DESCRIPTIONS = {
    # Skills
    "Active Learning": "Rapidly absorbing new information and applying it on the job",
    "Active Listening": "Fully concentrating on what others say to understand their needs",
    "Complex Problem Solving": "Identifying tough problems and developing creative solutions",
    "Coordination": "Adjusting actions in relation to others' work to stay in sync",
    "Critical Thinking": "Using logic and reasoning to evaluate options and decisions",
    "Equipment Maintenance": "Performing routine maintenance to keep equipment running",
    "Equipment Selection": "Choosing the right tools and equipment for a job",
    "Installation": "Installing equipment, machines, wiring, or programs",
    "Instructing": "Teaching others how to do something effectively",
    "Judgment and Decision Making": "Weighing costs, benefits, and risks to make smart calls",
    "Learning Strategies": "Choosing the best training methods for learning new things",
    "Management of Financial Resources": "Planning and tracking budgets and expenditures",
    "Management of Material Resources": "Obtaining and managing supplies and materials efficiently",
    "Management of Personnel Resources": "Motivating, developing, and directing people on the job",
    "Mathematics": "Using math to solve real-world problems and analyze data",
    "Monitoring": "Tracking performance of yourself, others, or processes",
    "Negotiation": "Bringing others together and trying to reconcile differences",
    "Operation Monitoring": "Watching gauges, dials, and indicators to ensure proper operation",
    "Operation and Control": "Controlling equipment or systems operations",
    "Operations Analysis": "Analyzing needs and requirements to create a design",
    "Operations Monitoring": "Watching gauges, dials, and indicators to ensure proper operation",
    "Persuasion": "Convincing others to change their minds or behavior",
    "Programming": "Writing computer programs for various purposes",
    "Quality Control Analysis": "Conducting tests and inspections to evaluate quality",
    "Reading Comprehension": "Understanding written documents, reports, and procedures",
    "Repairing": "Fixing machines or systems using the needed tools",
    "Science": "Using scientific rules and methods to solve problems",
    "Service Orientation": "Actively looking for ways to help people",
    "Social Perceptiveness": "Being aware of others' reactions and understanding why they react that way",
    "Speaking": "Talking to others clearly and effectively to convey information",
    "Systems Analysis": "Determining how a system should work and how changes affect outcomes",
    "Systems Evaluation": "Identifying measures of system performance and improvement actions",
    "Technology Design": "Generating or adapting equipment and technology to serve user needs",
    "Time Management": "Managing your own time and the time of others",
    "Troubleshooting": "Determining causes of operating errors and deciding what to do",
    "Writing": "Communicating effectively through written documents and reports",
    # Knowledge
    "Administration and Management": "Business and management principles for strategic planning and resource allocation",
    "Biology": "Knowledge of plant and animal organisms and their interactions",
    "Building and Construction": "Materials, methods, and tools for constructing buildings and infrastructure",
    "Chemistry": "The composition, structure, and properties of substances and their reactions",
    "Clerical": "Administrative and clerical procedures, systems, and record-keeping",
    "Communications and Media": "Media production, communication, and dissemination techniques",
    "Computers and Electronics": "Circuit boards, processors, electronic equipment, and software",
    "Customer and Personal Service": "Principles for providing quality customer service and satisfaction",
    "Design": "Design techniques, tools, and principles for production of plans and drawings",
    "Economics and Accounting": "Economic and accounting principles, markets, and financial reporting",
    "Education and Training": "Principles and methods for curriculum design, teaching, and instruction",
    "Engineering and Technology": "Applying engineering science and technology to practical problems",
    "English Language": "The structure and content of English including meaning and grammar",
    "Fine Arts": "Theory and techniques for visual arts, music, dance, and drama",
    "Food Production": "Techniques and equipment for planting, growing, and harvesting food products",
    "Foreign Language": "The structure and content of a foreign language",
    "Geography": "Principles for describing land, sea, and air masses and their features",
    "History and Archeology": "Historical events and their causes, indicators, and effects",
    "Law and Government": "Laws, legal codes, government regulations, and the political process",
    "Mathematics": "Arithmetic, algebra, geometry, calculus, statistics, and their applications",
    "Mechanical": "Machines and tools including their designs, uses, and maintenance",
    "Medicine and Dentistry": "Information needed to diagnose and treat human injuries and diseases",
    "Personnel and Human Resources": "Principles for recruitment, selection, training, and labor relations",
    "Philosophy and Theology": "Different philosophical systems and religions and their principles",
    "Physics": "Physical principles, laws, and applications including air, water, and dynamics",
    "Production and Processing": "Raw materials, production processes, quality control, and costs",
    "Psychology": "Human behavior, individual differences, and methods of assessment",
    "Public Safety and Security": "Equipment, policies, and strategies for protecting people and property",
    "Sales and Marketing": "Principles and methods for showing, promoting, and selling products",
    "Sociology and Anthropology": "Group behavior and dynamics, societal trends, and cultural influences",
    "Telecommunications": "Transmission, broadcasting, switching, control of telecommunications systems",
    "Therapy and Counseling": "Principles for diagnosis, treatment, and rehabilitation of physical/mental dysfunctions",
    "Transportation": "Principles and methods for moving people or goods by air, rail, sea, or road",
}


def read_tsv(filepath):
    """Read a tab-separated O*NET file. Returns list of dicts."""
    rows = []
    if not os.path.exists(filepath):
        print(f"  WARNING: File not found: {filepath}")
        return rows
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    print(f"  Loaded {len(rows)} rows from {os.path.basename(filepath)}")
    return rows


def load_occupation_titles(filepath):
    """Load occupation titles from Occupation Data.txt"""
    titles = {}
    if not os.path.exists(filepath):
        print(f"  WARNING: File not found: {filepath}")
        return titles
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            code = row.get("O*NET-SOC Code", "").strip()
            title = row.get("Title", "").strip()
            if code and title:
                titles[code] = title
    print(f"  Loaded {len(titles)} occupation titles")
    return titles


def parse_onet_data(skills_rows, knowledge_rows):
    """
    Parse skills and knowledge data into a nested dict:
      occ_code -> skill_name -> {"im": float, "lv": float, "type": "skill"|"knowledge"}

    Only includes rows where Recommend Suppress == "N".
    """
    data = defaultdict(lambda: defaultdict(dict))

    for row in skills_rows:
        if row.get("Recommend Suppress", "").strip() != "N":
            continue
        code = row.get("O*NET-SOC Code", "").strip()
        name = row.get("Element Name", "").strip()
        scale = row.get("Scale ID", "").strip()
        try:
            value = float(row.get("Data Value", "0"))
        except (ValueError, TypeError):
            continue
        if not code or not name:
            continue

        if scale == "IM":
            data[code][name]["im"] = value
            data[code][name]["type"] = "skill"
        elif scale == "LV":
            data[code][name]["lv"] = value
            data[code][name]["type"] = "skill"

    for row in knowledge_rows:
        if row.get("Recommend Suppress", "").strip() != "N":
            continue
        code = row.get("O*NET-SOC Code", "").strip()
        name = row.get("Element Name", "").strip()
        scale = row.get("Scale ID", "").strip()
        try:
            value = float(row.get("Data Value", "0"))
        except (ValueError, TypeError):
            continue
        if not code or not name:
            continue

        if scale == "IM":
            data[code][name]["im"] = value
            data[code][name]["type"] = "knowledge"
        elif scale == "LV":
            data[code][name]["lv"] = value
            data[code][name]["type"] = "knowledge"

    return data


def get_skill_color(rank):
    """Assign color variable based on skill rank (0-indexed)."""
    if rank < 3:
        return "var(--accent)"
    elif rank < 5:
        return "var(--teal)"
    elif rank < 7:
        return "var(--blue)"
    else:
        return "var(--purple)"


def get_hedge_color(pct):
    """Assign color variable based on hedge percentage."""
    if pct >= 75:
        return "var(--teal)"
    elif pct >= 60:
        return "var(--accent)"
    else:
        return "var(--purple)"


def aggregate_skills_for_group(occ_codes, onet_data, occupation_titles, group_name, is_major=True, category=None):
    """
    For a group of occupation codes, aggregate skills data.
    Returns dict with skills, careers, hedgePct, hedgeColor, insight.
    """
    # Filter to codes that exist in our data
    valid_codes = [c for c in occ_codes if c in onet_data]
    total_occs = len(valid_codes)

    if total_occs == 0:
        return {
            "skills": [],
            "careers": [],
            "hedgePct": 0,
            "hedgeColor": "var(--purple)",
            "insight": f"Data not yet available for {group_name}."
        }

    # Collect all skill names across occupations
    all_skills = defaultdict(lambda: {"im_sum": 0, "lv_sum": 0, "count": 0, "high_count": 0, "type": "skill"})

    for code in valid_codes:
        for skill_name, vals in onet_data[code].items():
            im = vals.get("im", 0)
            lv = vals.get("lv", 0)
            all_skills[skill_name]["im_sum"] += im
            all_skills[skill_name]["lv_sum"] += lv
            all_skills[skill_name]["count"] += 1
            all_skills[skill_name]["type"] = vals.get("type", "skill")
            if im >= 3.5:
                all_skills[skill_name]["high_count"] += 1

    # Compute coverage % and averages, then rank
    skill_list = []
    for name, vals in all_skills.items():
        if vals["count"] == 0:
            continue
        coverage_pct = round((vals["high_count"] / total_occs) * 100)
        avg_im = vals["im_sum"] / vals["count"]
        avg_lv = vals["lv_sum"] / vals["count"]
        skill_list.append({
            "name": name,
            "pct": coverage_pct,
            "avg_im": avg_im,
            "avg_lv": avg_lv,
            "type": vals["type"],
            "high_count": vals["high_count"]
        })

    # Sort by coverage %, then by average importance
    skill_list.sort(key=lambda x: (x["pct"], x["avg_im"]), reverse=True)

    # Take top 10 skills
    top_skills = skill_list[:10]

    # Assign colors and descriptions
    formatted_skills = []
    for i, s in enumerate(top_skills):
        desc = SKILL_DESCRIPTIONS.get(s["name"], f"Proficiency in {s['name'].lower()} relevant to this field")
        formatted_skills.append({
            "name": s["name"],
            "desc": desc,
            "pct": s["pct"],
            "color": get_skill_color(i)
        })

    # Build careers list
    careers = []
    for code in valid_codes:
        title = occupation_titles.get(code, "")
        if title:
            salary = SALARY_MAP.get(code, "$45K-$85K")
            careers.append({"title": title, "salary": salary})
    # Deduplicate by title
    seen_titles = set()
    unique_careers = []
    for c in careers:
        if c["title"] not in seen_titles:
            seen_titles.add(c["title"])
            unique_careers.append(c)
    careers = unique_careers[:12]  # Cap at 12

    # Compute hedge percentage
    # Top 3 skills: what % of occupations have at least one of these at importance >= 3.5?
    if len(top_skills) >= 3:
        top3_names = [s["name"] for s in top_skills[:3]]
        covered_occs = set()
        for code in valid_codes:
            for skill_name in top3_names:
                if skill_name in onet_data[code]:
                    if onet_data[code][skill_name].get("im", 0) >= 3.5:
                        covered_occs.add(code)
                        break
        hedge_pct = round((len(covered_occs) / total_occs) * 100) if total_occs > 0 else 0
    else:
        hedge_pct = 0

    hedge_color = get_hedge_color(hedge_pct)

    # Generate insight text
    if len(top_skills) >= 3:
        top3_str = " + ".join([s["name"] for s in top_skills[:3]])
        top_pct = top_skills[0]["pct"]
        insight = (
            f"<strong>{top3_str}</strong> cover {hedge_pct}% of career paths in this area. "
            f"{top_skills[0]['name']} alone shows up in {top_pct}% of roles — "
            f"start there and branch out."
        )
    elif len(top_skills) >= 1:
        insight = (
            f"<strong>{top_skills[0]['name']}</strong> is the most transferable skill at "
            f"{top_skills[0]['pct']}% coverage. Build that foundation first."
        )
    else:
        insight = f"Explore roles in {group_name} to find your starting point."

    result = {
        "skills": formatted_skills,
        "careers": careers,
        "hedgePct": hedge_pct,
        "hedgeColor": hedge_color,
        "insight": insight
    }

    if is_major and category:
        result["category"] = category

    return result


def main():
    print("=" * 60)
    print("build_skills_data.py — Building skills explorer data")
    print("=" * 60)

    # Load mapping files
    print("\nLoading mapping files...")
    with open(MAJOR_MAP_PATH, "r") as f:
        major_map = json.load(f)
    print(f"  Loaded {len(major_map)} majors")

    with open(SECTOR_MAP_PATH, "r") as f:
        sector_map = json.load(f)
    print(f"  Loaded {len(sector_map)} sectors")

    # Load O*NET data files
    print("\nLoading O*NET data files...")
    skills_rows = read_tsv(SKILLS_FILE)
    knowledge_rows = read_tsv(KNOWLEDGE_FILE)
    occupation_titles = load_occupation_titles(OCCUPATION_FILE)

    if not skills_rows and not knowledge_rows:
        print("\nWARNING: No O*NET data files found. Generating output with empty skills.")
        print("Place Skills.txt, Knowledge.txt, and 'Occupation Data.txt' in the onet_data/ directory.")

    # Parse into structured data
    print("\nParsing O*NET data...")
    onet_data = parse_onet_data(skills_rows, knowledge_rows)
    print(f"  Parsed data for {len(onet_data)} occupations")

    # Process majors
    print("\nProcessing majors...")
    majors_output = {}
    for major_name, major_info in major_map.items():
        occ_codes = major_info.get("occupations", [])
        category = major_info.get("category", "Other")
        result = aggregate_skills_for_group(
            occ_codes, onet_data, occupation_titles,
            major_name, is_major=True, category=category
        )
        majors_output[major_name] = result
        valid = len([c for c in occ_codes if c in onet_data])
        print(f"  {major_name}: {valid}/{len(occ_codes)} occupations matched, "
              f"{len(result['skills'])} skills, hedge={result['hedgePct']}%")

    # Process sectors
    print("\nProcessing sectors...")
    sectors_output = {}
    for sector_name, sector_info in sector_map.items():
        occ_codes = sector_info.get("occupations", [])
        result = aggregate_skills_for_group(
            occ_codes, onet_data, occupation_titles,
            sector_name, is_major=False
        )
        sectors_output[sector_name] = result
        valid = len([c for c in occ_codes if c in onet_data])
        print(f"  {sector_name}: {valid}/{len(occ_codes)} occupations matched, "
              f"{len(result['skills'])} skills, hedge={result['hedgePct']}%")

    # Build final output
    output = {
        "majors": majors_output,
        "sectors": sectors_output
    }

    # Write output
    print(f"\nWriting output to {OUTPUT_PATH}...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    file_size = os.path.getsize(OUTPUT_PATH)
    print(f"  Output file size: {file_size:,} bytes")

    # Summary stats
    total_majors_with_skills = sum(1 for m in majors_output.values() if len(m["skills"]) > 0)
    total_sectors_with_skills = sum(1 for s in sectors_output.values() if len(s["skills"]) > 0)
    print(f"\nSummary:")
    print(f"  Majors with skills data: {total_majors_with_skills}/{len(majors_output)}")
    print(f"  Sectors with skills data: {total_sectors_with_skills}/{len(sectors_output)}")
    print(f"  Output: {OUTPUT_PATH}")
    print("\nDone!")


if __name__ == "__main__":
    main()
