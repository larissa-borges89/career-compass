"""
Mock data for development and testing.
When MOCK_APIS=true, all external API calls return this data instead.
Zero API credits consumed during development.
"""

MOCK_JOBS = [
    {
        "title": "Senior Full Stack Developer",
        "company": "TechCorp NYC",
        "location": "New York, NY",
        "description": "We are looking for a Senior Full Stack Developer with .NET Core, React, and Angular experience. Must have 5+ years of experience with cloud platforms (AWS/Azure) and CI/CD pipelines.",
        "url": "https://example.com/jobs/1",
        "source": "adzuna",
        "date": "2026-04-14",
        "days_old": 1,
    },
    {
        "title": "Software Engineer - React & Node.js",
        "company": "StartupHub",
        "location": "Brooklyn, NY",
        "description": "Join our growing team! We need a Software Engineer proficient in React, Node.js, TypeScript and PostgreSQL. Experience with AWS and Docker is a plus.",
        "url": "https://example.com/jobs/2",
        "source": "serpapi",
        "date": "2026-04-13",
        "days_old": 2,
    },
    {
        "title": "Full Stack Engineer - .NET Angular",
        "company": "FinTech Solutions",
        "location": "Manhattan, NY",
        "description": "Full Stack Engineer needed for our financial platform. Stack: .NET Core, Angular 17, Azure DevOps, SQL Server. Healthcare domain experience preferred.",
        "url": "https://example.com/jobs/3",
        "source": "adzuna",
        "date": "2026-04-14",
        "days_old": 1,
    },
    {
        "title": "Power BI Developer",
        "company": "DataViz Corp",
        "location": "New York, NY",
        "description": "Power BI Developer with strong SQL and DAX skills. Experience with Azure Data Factory and data modeling required.",
        "url": "https://example.com/jobs/4",
        "source": "serpapi",
        "date": "2026-04-12",
        "days_old": 3,
    },
    {
        "title": "Backend Engineer - C# .NET",
        "company": "CloudSystems Inc",
        "location": "Remote / New York",
        "description": "Backend Engineer to build microservices in C# .NET 8. Must know REST APIs, Azure Service Bus, and have experience with distributed systems.",
        "url": "https://example.com/jobs/5",
        "source": "adzuna",
        "date": "2026-04-14",
        "days_old": 1,
    },
]

MOCK_MATCH_RESULTS = [
    {**job, "match_score": score, "match_verdict": verdict, "match_reason": reason,
     "matching_skills": matching, "missing_skills": missing}
    for job, score, verdict, reason, matching, missing in zip(
        MOCK_JOBS,
        [88, 82, 91, 74, 79],
        ["strong_match", "strong_match", "strong_match", "good_match", "good_match"],
        [
            "Strong alignment with full-stack .NET and React skills. Cloud experience matches well.",
            "React and Node.js match your frontend profile. TypeScript is a strength.",
            "Excellent match — .NET Core + Angular is your primary stack. Healthcare domain is a bonus.",
            "Power BI and SQL align with your data analytics experience. DAX may need brushing up.",
            "C# .NET backend role fits your profile. Distributed systems experience is relevant.",
        ],
        [
            ["Full-Stack Development", ".NET Core", "React", "Angular", "Azure"],
            ["React", "Node.js", "TypeScript", "PostgreSQL"],
            [".NET Core", "Angular", "Azure DevOps", "Full-Stack Development"],
            ["Power BI", "SQL", "Data Analytics", "Azure"],
            ["C#", ".NET Core", "REST APIs", "Azure"],
        ],
        [
            ["CI/CD pipeline specifics"],
            ["Docker (explicit)"],
            ["SQL Server (explicit)"],
            ["DAX", "Azure Data Factory"],
            ["Azure Service Bus", "Microservices at scale"],
        ],
    )
]

MOCK_KEYWORDS = [
    "Full-Stack Developer .NET Angular",
    "Software Engineer React Node.js",
    "Power BI Data Analytics Developer",
    "C# .NET Core Software Engineer",
    "Healthcare Software Engineer",
]

MOCK_EMAIL_CLASSIFICATIONS = [
    {
        "email": "Thank you for applying to Software Engineer at TechCorp",
        "from": "recruiting@techcorp.com",
        "date": "2026-04-14",
        "status": "applied",
        "summary": "Application received for Software Engineer position.",
    },
    {
        "email": "Interview invitation - Full Stack Developer at FinTech Solutions",
        "from": "hr@fintechsolutions.com",
        "date": "2026-04-13",
        "status": "interview_scheduled",
        "summary": "Invited to interview for Full Stack Developer role.",
    },
    {
        "email": "Update on your application at StartupHub",
        "from": "noreply@startuphub.com",
        "date": "2026-04-12",
        "status": "rejected",
        "summary": "Application not moving forward at this time.",
    },
]
