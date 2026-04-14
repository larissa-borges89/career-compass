from src.tracker import add_application, list_applications, update_status, sync_emails_to_tracker


def show_menu():
    print("\n=== Career Compass ===")
    print("1. Add application")
    print("2. List applications")
    print("3. Update status")
    print("4. Sync emails to tracker")
    print("5. Find matching jobs")
    print("6. Exit")
    return input("\nChoose an option: ")


def handle_add():
    company = input("Company: ")
    role = input("Role: ")
    notes = input("Notes (optional): ")
    app = add_application(company, role, notes=notes)
    print(f"\nAdded: {app['role']} at {app['company']} (ID: {app['id']})")


def handle_list():
    apps = list_applications()
    if not apps:
        print("\nNo applications yet.")
        return
    print(f"\n{'ID':<5} {'Company':<20} {'Role':<25} {'Status':<15} {'Date':<12}")
    print("-" * 77)
    for app in apps:
        date = app['created_at'][:10]
        print(f"{app['id']:<5} {app['company']:<20} {app['role']:<25} {app['status']:<15} {date:<12}")


def handle_update():
    handle_list()
    app_id = int(input("\nEnter application ID to update: "))
    print("\nStatuses: applied | interview_scheduled | offer | rejected")
    new_status = input("New status: ")
    app = update_status(app_id, new_status)
    if app:
        print(f"\nUpdated: {app['company']} -> {app['status']}")
    else:
        print("\nApplication not found.")


def handle_job_search():
    from src.resume_parser import parse_resume
    from src.job_search import search_jobs, filter_ghost_jobs
    from src.job_matcher import match_jobs, print_matches, generate_search_keywords
    import os

    resume_path = "resume.pdf"
    if not os.path.exists(resume_path):
        resume_path = input("Resume path (PDF or DOCX): ").strip()

    print("\nLoading your profile...")
    profile = parse_resume(resume_path)
    print(f"Profile loaded: {profile['name']} — {profile['title']}")

    print("\nGenerating search keywords from your profile...")
    keywords = generate_search_keywords(profile)
    print(f"Keywords: {keywords}")

    location = input("\nLocation (default: New York): ").strip() or "New York"
    max_days = input("Max job age in days (default: 2): ").strip()
    max_days = int(max_days) if max_days.isdigit() else 2

    all_jobs = []
    seen = set()
    for keyword in keywords[:3]:
        jobs = search_jobs(keyword, location)
        active = filter_ghost_jobs(jobs, max_days=max_days)
        for job in active:
            key = f"{job['title'].lower()}_{job['company'].lower()}"
            if key not in seen:
                seen.add(key)
                all_jobs.append(job)

    print(f"\nTotal unique active jobs found: {len(all_jobs)}")

    if not all_jobs:
        print("No active jobs found. Try increasing max job age.")
        return

    min_score = input("Minimum match score 0-100 (default: 60): ").strip()
    min_score = int(min_score) if min_score.isdigit() else 60

    matches = match_jobs(profile, all_jobs, min_score=min_score)
    print_matches(matches)

    if matches:
        save = input("Save matches to tracker? (y/n): ").strip().lower()
        if save == "y":
            for job in matches:
                add_application(
                    company=job["company"],
                    role=job["title"],
                    status="applied",
                    notes=f"Match: {job['match_score']}/100 — {job['match_reason']}"
                )
            print(f"\nSaved {len(matches)} jobs to tracker.")


def main():
    while True:
        choice = show_menu()
        if choice == "1":
            handle_add()
        elif choice == "2":
            handle_list()
        elif choice == "3":
            handle_update()
        elif choice == "4":
            sync_emails_to_tracker()
        elif choice == "5":
            handle_job_search()
        elif choice == "6":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option.")


if __name__ == "__main__":
    main()
