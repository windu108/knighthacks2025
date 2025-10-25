
activites = []
users = []


def logout(username):
    users.pop(username)

def userLogin():
    username = input("Enter username: ")
    users.append(username)


def add_activity():
    member = users.get('member_name')
    name = activities.get['activity_name'].strip()
    if name:
        activities.append({
            'name': name,
            'votes': 0,
            'suggested_by': member,
            'voters': []
        })

def main():
    decision = input("Do you want to login? (yes/no): ")
    if(decision == "yes"):
        userLogin()
main()