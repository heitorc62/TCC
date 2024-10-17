from options import *

# The main function for handling user input
def handle_admin_input(input_option):
    if input_option == 1:
        register_admin()
    elif input_option == 2:
        login_admin()
    elif input_option == 3:
        send_invitation()
    elif input_option == 4:
        update_tomato_dataset()
    elif input_option == 5:
        update_model()
    elif input_option == 6:
        retrain_model()
    elif input_option == 0:
        exit()
    else:
        print("Invalid input, please try again.")
        return

# The main loop for the CLI program
if __name__ == "__main__":
    print("Welcome to the admin panel for the tomato server!")
    while True:
        print("Please select an option:")
        print("1. Register a new admin")
        print("2. Login with admin credentials")
        print("3. Send invitation to a reviewer")
        print("4. Update the tomato dataset with the reviewed images")
        print("5. Update model given a presigned URL")
        print("6. Retrain the model with updated dataset")
        print("0. Exit")
        try:
            input_option = int(input("Enter your choice: "))
            handle_admin_input(input_option)
        except ValueError:
            print("Invalid input, please enter a number.")
