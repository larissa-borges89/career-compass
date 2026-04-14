import os
import json
import re
from dotenv import load_dotenv

load_dotenv()


def match_job(profile, job):
    """
    Use Claude AI to score how well a candidate matches a job.
    Returns a score 0-100 and a brief explanation.
    """
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""You are a senior tech recruiter. Evaluate how well this candidate matches this job.

CANDIDATE PROFILE:
- Name: {profile.get('name')}
- Title: {profile.get('title')}
- Seniority: {profile.get('seniority')}
- Experience: {profile.get('experience_years')} years
- Skills: {', '.join(profile.get('skills', []))}
- Languages: {', '.join(profile.get('languages', []))}
- Industries: {', '.join(profile.get('industries', []))}
- Last role: {profile.get('last_role')} at {profile.get('last_company')}

JOB POSTING:
- Title: {job.get('title')}
- Company: {job.get('company')}
- Location: {job.get('location')}
- Description: {job.get('description', '')[:500]}

Respond ONLY with this JSON format:
{{
  "score": 0,
  "verdict": "strong_match|good_match|weak_match|no_match",
  "reason": "one sentence explaining the score",
  "missing_skills": ["skill1", "skill2"],
  "matching_skills": ["skill1", "skill2"]
}}"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def match_jobs(profile, jobs, min_score=60):
    """
    Match candidate profile against a list of jobs.
    Returns jobs sorted by score, filtered by min_score.
    """
    print(f"\nMatching {len(jobs)} jobs against your profile...\n")

    matched = []
    for i, job in enumerate(jobs):
        print(f"  Analyzing {i+1}/{len(jobs)}: {job['title']} at {job['company']}...")
        result = match_job(profile, job)
        job["match_score"] = result.get("score", 0)
        job["match_verdict"] = result.get("verdict", "")
        job["match_reason"] = result.get("reason", "")
        job["missing_skills"] = result.get("missing_skills", [])
        job["matching_skills"] = result.get("matching_skills", [])

        if job["match_score"] >= min_score:
            matched.append(job)

    matched.sort(key=lambda x: x["match_score"], reverse=True)
    print(f"\nFound {len(matched)} jobs with score >= {min_score}\n")
    return matched


def print_matches(jobs):
    """Print matched jobs in a readable format."""
    if not jobs:
        print("No matches found.")
        return

    for job in jobs:
        score = job["match_score"]
        verdict = job["match_verdict"]
        emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"

        print(f"{emoji} [{score}/100] {job['title']}")
        print(f"   Company:  {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Verdict:  {verdict}")
        print(f"   Reason:   {job['match_reason']}")
        if job["matching_skills"]:
            print(f"   Matches:  {', '.join(job['matching_skills'][:5])}")
        if job["missing_skills"]:
            print(f"   Missing:  {', '.join(job['missing_skills'][:3])}")
        print(f"   URL:      {job.get('url', 'N/A')}")
        print()


def generate_search_keywords(profile):
    """Use Claude AI to generate optimal job search keywords from profile."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""Based on this candidate profile, suggest 5 optimal job search keywords.
Focus on their strongest skills and most recent experience.
Avoid too broad or too narrow terms.
Seniority is for context only — do not restrict keywords by level.

Profile:
- Title: {profile.get('title')}
- Skills: {', '.join(profile.get('skills', [])[:10])}
- Languages: {', '.join(profile.get('languages', []))}
- Seniority: {profile.get('seniority')} (use for context only, not as a filter)
- Industries: {', '.join(profile.get('industries', []))}

Respond ONLY with a JSON array of 5 strings:
["keyword 1", "keyword 2", "keyword 3", "keyword 4", "keyword 5"]"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)
