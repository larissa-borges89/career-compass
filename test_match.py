from src.resume_parser import parse_resume
from src.job_search import search_jobs, filter_ghost_jobs
from src.job_matcher import match_jobs, print_matches, generate_search_keywords

# Load profile from cache
profile = parse_resume('resume.pdf')

# Generate smart keywords from profile
print("Generating search keywords from your profile...")
keywords = generate_search_keywords(profile)
print(f"Keywords: {keywords}\n")

# Search with each keyword and merge results
all_jobs = []
seen = set()
for keyword in keywords[:3]:  # Use top 3 to save API calls
    jobs = search_jobs(keyword, 'New York')
    active = filter_ghost_jobs(jobs)
    for job in active:
        key = f"{job['title'].lower()}_{job['company'].lower()}"
        if key not in seen:
            seen.add(key)
            all_jobs.append(job)

print(f"\nTotal unique active jobs: {len(all_jobs)}")

# Match against profile
matches = match_jobs(profile, all_jobs, min_score=60)
print_matches(matches)
