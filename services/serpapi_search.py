import os
import requests
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

def search_jobs_serpapi(query: str, count: int = 10):
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY environment variable not set.")
    params = {
        "q": query,
        "engine": "google_jobs",  # Use Google Jobs engine for job postings
        "api_key": SERPAPI_KEY,
        "num": count
    }
    resp = requests.get("https://serpapi.com/search", params=params)
    resp.raise_for_status()
    data = resp.json()
    jobs_results = data.get("jobs_results", [])
    jobs = []
    seen_keys = set()
    for job in jobs_results:
        title = job.get("title", "Job Listing")
        company = job.get("company_name", "")
        location = job.get("location", "")
        job_key = (title.strip().lower(), company.strip().lower(), location.strip().lower())
        apply_options = job.get("apply_options", [])
        if apply_options:
            for option in apply_options:
                link = option.get("link")
                if link and job_key not in seen_keys:
                    jobs.append({
                        "title": f"{title} at {company} ({location})",
                        "link": link
                    })
                    seen_keys.add(job_key)
                    if len(jobs) >= count:
                        return jobs
        else:
            link = job.get("share_link") or job.get("url")
            if link and job_key not in seen_keys:
                jobs.append({
                    "title": f"{title} at {company} ({location})",
                    "link": link
                })
                seen_keys.add(job_key)
                if len(jobs) >= count:
                    return jobs
    if not jobs:
        results = data.get("organic_results", [])
        for r in results:
            title = r.get("title", "Job Listing")
            link = r.get("link", "")
            job_key = (title.strip().lower(), '', '')
            if link and job_key not in seen_keys:
                jobs.append({"title": title, "link": link})
                seen_keys.add(job_key)
                if len(jobs) >= count:
                    break
    return jobs[:count] 