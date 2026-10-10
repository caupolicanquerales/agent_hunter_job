#!/usr/bin/env python3
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENCODE_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
PROJECT_DIR = os.path.dirname(OPENCODE_DIR)
OUTPUT_DIR = os.path.join(OPENCODE_DIR, "opportunities")
PORTALS_PATH = os.path.join(BASE_DIR, "constants", "job_portals.js")
REPORT_PATH = os.path.join(PROJECT_DIR, "reports", "job_opportunities.js")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_portal_group(portals_path, object_name):
    """Load one JS object such as FEEDS_RSS or APIS_JSON from the portal config file."""
    with open(portals_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    match = re.search(
        rf"export\s+const\s+{object_name}\s*=\s*(\{{[\s\S]*?\}})\s*(?:;)?(?=\s*export\s+const|\s*$)",
        content,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"Could not parse {object_name} from {portals_path}")

    cleaned = re.sub(r",\s*(\]|\})", r"\1", match.group(1))
    return json.loads(cleaned)


FEEDS_RSS = load_portal_group(PORTALS_PATH, "FEEDS_RSS")
APIS_JSON = load_portal_group(PORTALS_PATH, "APIS_JSON")
APIS_GENERIC = load_portal_group(PORTALS_PATH, "APIS_GENERIC")

PORTAL_GROUPS = {
    "rss": FEEDS_RSS,
    "remoteok": APIS_JSON,
    "generic": APIS_GENERIC,
}

PORTAL_FETCHERS = {
    "rss": lambda url, source_name: fetch_rss(url, source_name),
    "remoteok": lambda url, source_name: fetch_remoteok(url, source_name),
    "generic": lambda url, source_name: fetch_json_jobs(url, source_name),
}

KEYWORDS = ["java", "spring", "backend", "microservices", "architecture", "ai"]

def clean_html(raw_html):
    """Strip HTML tags to keep context tokens minimal."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return " ".join(cleantext.split())


def extract_salary(text):
    """Try to find salary information from a string like '$120k - $150k' or '80,000 USD'."""
    if not text:
        return "N/A"

    patterns = [
        r"\$\s?\d{1,3}(?:,\d{3})?(?:\.\d{2})?\s*(?:k|K|m|M)?\s*(?:[-–to]+)\s*\$\s?\d{1,3}(?:,\d{3})?(?:\.\d{2})?\s*(?:k|K|m|M)?",
        r"\$\s?\d{1,3}(?:,\d{3})?(?:\.\d{2})?\s*(?:k|K|m|M)?\s*(?:per\s*year|annual|yr|/yr|USD|EUR|GBP)",
        r"\d{4,6}\s*(?:USD|EUR|GBP|CAD|AUD)\s*(?:per\s*year|annual|/yr)",
        r"\d{2,3}(?:\.\d+)?\s*(?:k|K|m|M)\s*(?:[-–to]+)\s*\d{2,3}(?:\.\d+)?\s*(?:k|K|m|M)",
        r"(?:€|£|¥|\$)\s?\d{1,3}(?:,\d{3})?(?:\.\d{2})?\s*(?:k|K|m|M)?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return "N/A"


def extract_currency(text):
    if not text:
        return "N/A"

    currency_map = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        'usd': 'USD',
        'eur': 'EUR',
        'gbp': 'GBP',
        'cad': 'CAD',
        'aud': 'AUD',
        'jpy': 'JPY'
    }

    for symbol, code in currency_map.items():
        if symbol in text.lower() or symbol in text:
            return code

    match = re.search(r"\b(?:USD|EUR|GBP|CAD|AUD|JPY)\b", text, re.IGNORECASE)
    if match:
        return match.group(0).upper()

    return "N/A"


def extract_salary_period(text):
    if not text:
        return "N/A"

    lowered = text.lower()
    if any(token in lowered for token in ["per day", "/day", "daily"]):
        return "day"
    if any(token in lowered for token in ["per month", "/mo", "monthly", "month"]):
        return "month"
    if any(token in lowered for token in ["per year", "/yr", "annual", "annually", "yearly", "salary"]):
        return "year"
    return "N/A"


def normalize_salary_details(text):
    salary_value = extract_salary(text)
    return {
        "salary": salary_value,
        "salary_currency": extract_currency(text),
        "salary_period": extract_salary_period(text),
    }


def extract_years_experience(text):
    """Try to find experience requirements like '3+ years' or 'minimum 5 years'."""
    if not text:
        return "N/A"

    patterns = [
        r"(?:minimum|at\s*least|\+|\+\s*years?|\babout\b|\bwith\b)\s*(?:\d+\.?\d*\s*[-–to]\s*\d+\.?\d*|\d+\.?\d*)\s*\+?\s*years?\s*(?:of\s*)?experience",
        r"\b\d+\.?\d*\s*\+?\s*years?\b",
        r"\b(?:senior|lead|principal)\b.*\b\d+\+\s*years?\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return "N/A"


def fetch_rss(url, source_name="WeWorkRemotely"):
    jobs = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else "N/A"
                link = item.find('link').text if item.find('link') is not None else "N/A"
                desc = item.find('description').text if item.find('description') is not None else ""
                
                # Pre-filter by relevant keywords before passing to LLM
                combined_text = f"{title} {desc}".lower()
                if any(kw in combined_text for kw in KEYWORDS):
                    cleaned_desc = clean_html(desc)[:1500]
                    salary_text = f"{title} {cleaned_desc}"
                    salary_info = normalize_salary_details(salary_text)
                    years_experience = extract_years_experience(salary_text)
                    jobs.append({
                        "title": title,
                        "link": link,
                        "source": source_name,
                        "salary": salary_info["salary"],
                        "salary_currency": salary_info["salary_currency"],
                        "salary_period": salary_info["salary_period"],
                        "years_experience": years_experience,
                        "description": cleaned_desc
                    })
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    return jobs

def fetch_remoteok(url, source_name="RemoteOK"):
    jobs = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if not isinstance(data, list):
                print(f"Error fetching {source_name}: expected JSON list, got {type(data).__name__}")
                return []
            # RemoteOK returns metadata in index 0, actual jobs follow
            for item in data[1:15]:
                title = item.get('position', 'N/A')
                company = item.get('company', 'N/A')
                desc = item.get('description', '')
                url_link = item.get('url', 'N/A')
                cleaned_desc = clean_html(desc)[:1500]
                salary_value = item.get('salary') or item.get('salary_min') or item.get('salary_max')
                salary_text = f"{title} {cleaned_desc}"
                if salary_value is None:
                    salary_info = normalize_salary_details(salary_text)
                    salary = salary_info["salary"]
                    salary_currency = salary_info["salary_currency"]
                    salary_period = salary_info["salary_period"]
                else:
                    salary = str(salary_value)
                    salary_currency = extract_currency(f"{salary} {salary_text}")
                    salary_period = extract_salary_period(f"{salary} {salary_text}")

                jobs.append({
                    "title": f"{title} at {company}",
                    "company": company,
                    "location": item.get('location', 'N/A'),
                    "link": url_link,
                    "source": source_name,
                    "salary": salary,
                    "salary_currency": salary_currency,
                    "salary_period": salary_period,
                    "years_experience": extract_years_experience(salary_text),
                    "description": cleaned_desc
                })
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    return jobs


def fetch_json_jobs(url, source_name="GenericJSON"):
    """Fetch jobs from a JSON endpoint returning a list, or an object with a 'jobs' or 'data' key."""
    jobs = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        if isinstance(data, dict):
            data = data.get("jobs") or data.get("data")
        if not isinstance(data, list):
            print(f"Error fetching {source_name}: expected JSON list or 'jobs'/'data' key, got {type(data).__name__}")
            return []

        for item in data:
            if not isinstance(item, dict):
                continue
            category = str(item.get("category_name", "")).lower()
            if category and "development" not in category:
                continue
            title = item.get("title") or item.get("position") or item.get("jobTitle") or "N/A"
            company = (item.get("company_name") or item.get("company")
                       or item.get("companyName") or "N/A")
            link = (item.get("url") or item.get("link") or item.get("job_url")
                    or item.get("applicationLink") or "N/A")
            desc = item.get("description") or item.get("jobDescription") or item.get("jobExcerpt") or ""
            location = item.get("location") or item.get("jobGeo") or "N/A"
            if isinstance(location, list):
                location = ", ".join(str(part) for part in location)
            cleaned_desc = clean_html(desc)[:1500]
            salary_text = f"{title} {cleaned_desc}"
            if not any(kw in salary_text.lower() for kw in KEYWORDS):
                continue
            salary_info = normalize_salary_details(salary_text)
            salary_min = item.get("minSalary") or item.get("salaryMin")
            salary_max = item.get("maxSalary") or item.get("salaryMax")
            salary_currency = item.get("currency") or item.get("salaryCurrency") or salary_info["salary_currency"]
            if salary_min or salary_max:
                salary_value = " - ".join(str(part) for part in (salary_min, salary_max) if part is not None)
                salary_period = item.get("salaryPeriod") or salary_info["salary_period"]
                if salary_currency not in ("N/A", ""):
                    salary_value = f"{salary_value} {salary_currency}".strip()
            else:
                salary_value = salary_info["salary"]
                salary_period = salary_info["salary_period"]
            jobs.append({
                "title": f"{title} at {company}",
                "company": company,
                "location": location,
                "link": link,
                "source": source_name,
                "salary": salary_value,
                "salary_currency": salary_currency,
                "salary_period": salary_period,
                "years_experience": extract_years_experience(salary_text),
                "description": cleaned_desc
            })
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    return jobs


def fetch_jobs_from_portal(portal_name, portal_url, portal_kind):
    """Dispatch by the portal source kind (rss, remoteok or generic)."""
    fetcher = PORTAL_FETCHERS.get(portal_kind)
    if fetcher is None:
        print(f"No fetcher configured for portal kind: {portal_kind}")
        return []
    return fetcher(portal_url, portal_name)


def main():
    print("Fetching job listings from public sources...")
    all_jobs = []
    jobs_by_portal = {}

    for portal_kind, portal_group in PORTAL_GROUPS.items():
        for portal_name, portal_url in portal_group.items():
            portal_jobs = fetch_jobs_from_portal(portal_name, portal_url, portal_kind)
            jobs_by_portal[portal_name] = portal_jobs
            all_jobs.extend(portal_jobs)

    today = datetime.now().strftime("%Y-%m-%d")
    out_file = os.path.join(OUTPUT_DIR, f"raw_jobs_{today}.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("export const JOB_OPPORTUNITIES = ")
        json.dump(jobs_by_portal, f, indent=2, ensure_ascii=False)
        f.write(";\n")

    print(f"Successfully saved {len(all_jobs)} pre-filtered jobs to {out_file}")
    print(f"Successfully saved portal grouped opportunities to {REPORT_PATH}")

if __name__ == "__main__":
    main()