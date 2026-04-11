from src.tracker import add_application, list_applications, update_status

def show_menu():
    print("\n=== Career Compass ===")
    print("1. Add application")
    print("2. List applications")
    print("3. Update status")
    print("4. Exit")
    return input("\nChoose an option: ")

def handle_add():
    company = input("Company: ")
    role = input("Role: ")
    notes = input("Notes (optional): ")
    app = add_application(company, role, notes=notes)
    print(f"\n✅ Added: {app['role']} at {app['company']} (ID: {app['id']})")

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
        print(f"\n✅ Updated: {app['company']} → {app['status']}")
    else:
        print("\n❌ Application not found.")

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
            print("\nGoodbye! 👋")
            break
        else:
            print("\n❌ Invalid option.")

if __name__ == "__main__":
    main()