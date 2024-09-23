import requests, sys

# Define the base URL for the API
BASE_URL = "http://localhost:5000"

# Store JWT token globally after login
jwt_token = None

def get_auth_headers():
    """Returns the authorization headers with JWT token."""
    global jwt_token
    if jwt_token:
        return {"Authorization": f"Bearer {jwt_token}"}
    return {}

def login_admin():
    """Handles admin login and retrieves the JWT token."""
    global jwt_token
    if jwt_token:
        print("You are already logged in.")
        return

    username = input("Enter admin username: ")
    password = input("Enter admin password: ")

    # Send a POST request to the /admin_login endpoint to get the JWT
    response = requests.post(f"{BASE_URL}/admin_login", data={"username": username, "password": password})

    if response.status_code == 200:
        jwt_token = response.json().get('access_token')
        print("Login successful. JWT token received.")
    else:
        print(f"Login failed. Status Code: {response.status_code}, Message: {response.json().get('msg')}")

def send_invitation():
    """Sends an invitation email to a reviewer using JWT token."""
    if not jwt_token:
        print("Please log in as an admin first.")
        return

    email = input("Enter the reviewer's email address: ")

    # Send a POST request to the /invite_reviewer endpoint
    response = requests.post(f"{BASE_URL}/invite_reviewer", headers=get_auth_headers(), data={"email": email})

    if response.status_code == 200:
        print(f"Invitation sent to {email}.")
    else:
        print(f"Failed to send invitation. Status Code: {response.status_code}, Message: {response.json().get('msg')}")

def update_tomato_dataset():
    """Updates the tomato dataset with reviewed images using JWT token."""
    if not jwt_token:
        print("Please log in as an admin first.")
        return

    response = requests.post(f"{BASE_URL}/update_dataset", headers=get_auth_headers())

    if response.status_code == 200:
        print(f"Tomato dataset updated successfully.\n{response.body}")
    else:
        print(f"Failed to update dataset. Status Code: {response.status_code}, Message: {response.json().get('msg')}")

def retrain_model():
    """Retrains the model with the updated dataset using JWT token."""
    if not jwt_token:
        print("Please log in as an admin first.")
        return

    response = requests.post(f"{BASE_URL}/retrain_model", headers=get_auth_headers())

    if response.status_code == 200:
        print("Model retrained successfully.")
    else:
        print(f"Failed to retrain model. Status Code: {response.status_code}, Message: {response.json().get('msg')}")

def exit():
    """Exits the admin panel."""
    print("Exiting the admin panel. Goodbye!")
    sys.exit()