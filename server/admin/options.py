import requests, sys, paramiko, os
from dotenv import load_dotenv

# Define the base URL for the API
BASE_URL = "http://localhost:5000"

# Load environment variables from the .env file
load_dotenv()

# Store JWT token globally after login
jwt_token = None

def register_admin():
    """Registers a new admin user."""
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")

    # Send a POST request to the /admin_register endpoint
    response = requests.post(f"{BASE_URL}/register_admin", json={"username": username, "password": password})

    if response.status_code == 201:
        print("Admin user registered successfully.")
    else:
        print(f"Failed to register admin user. Status Code: {response.status_code}, Message: {response.json().get('msg')}")

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
    response = requests.post(f"{BASE_URL}/admin_login", json={"username": username, "password": password})

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
    response = requests.post(f"{BASE_URL}/invite_reviewer", headers=get_auth_headers(), json={"email": email})

    if response.status_code == 201:
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
    """SSH into the first machine (shell.vision.ime.usp.br), then SSH into the second machine (deepthree), and run the training script."""
    
    # Retrieve SSH credentials from environment variables
    shell_host = os.getenv("SSH_HOST")  # e.g., 'shell.vision.ime.usp.br'
    shell_user = os.getenv("SSH_USER")  # e.g., 'heitorc62'
    shell_password = os.getenv("SSH_PASSWORD")  # Your password for the shell machine
    
    gpu_host = os.getenv('GPU_SSH_HOST')
    gpu_user = os.getenv("SSH_USER")  # e.g., 'heitorc62'
    gpu_password = os.getenv("SSH_PASSWORD")  # Your password for the deepthree machine
    
    
    if not shell_host or not shell_user or not shell_password:
        print("Missing first machine SSH credentials. Please check your .env file.")
        return

    if not gpu_user or not gpu_password:
        print("Missing second machine SSH credentials. Please check your .env file.")
        return

    # Command to SSH into deepthree and run a script
    deepthree_command = f"ssh {gpu_host} 'bash /home/heitorc62/PlantsConv/TCC/Detector/remote_script.sh dataset-v2 weights-v2'"

    try:
        # Create an SSH client for the shell machine
        shell_ssh = paramiko.SSHClient()
        shell_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the shell machine
        shell_ssh.connect(hostname=shell_host, username=shell_user, password=shell_password)
        
        print(f"Connected to {shell_host}.")

        # SSH into the deepthree machine from the shell machine and run the script
        deepthree_ssh_command = f"sshpass -p {gpu_password} {deepthree_command}"

        stdin, stdout, stderr = shell_ssh.exec_command(deepthree_ssh_command)
        
        # Optional: Retrieve command output/errors
        output = stdout.read().decode()
        errors = stderr.read().decode()

        if errors:
            print(f"Error during the second SSH to deepthree: {errors}")
        else:
            print(f"Training process started successfully on deepthree. Output:\n{output}")
        
        # Close the SSH connection to the shell machine
        shell_ssh.close()

    except Exception as e:
        print(f"Failed to execute the remote script: {str(e)}")

def update_model():
    """Retrains the model by updating the weights using a presigned URL and S3 weights key."""
    if not jwt_token:
        print("Please log in as an admin first.")
        return

    # Get the presigned URL and S3 weights key from user input
    presigned_url = input("Please enter the presigned URL: ")
    s3_weights_key = input("Please enter the S3 weights key: ")

    # Prepare the payload with the presigned URL and the S3 key
    payload = {
        "weights_url": presigned_url,
        "weights_key": s3_weights_key
    }

    # Send the POST request to update the model weights using the previously discussed endpoint
    response = requests.post(f"{BASE_URL}/update_weights", json=payload, headers=get_auth_headers())

    # Handle the response
    if response.status_code == 200:
        print("Model update successfully with new weights.")
    else:
        print(f"Failed to update model. Status Code: {response.status_code}, Message: {response.json().get('error')}")


def exit():
    """Exits the admin panel."""
    print("Exiting the admin panel. Goodbye!")
    sys.exit()