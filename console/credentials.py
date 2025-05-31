from termcolor import colored
from prettytable import PrettyTable
from send_socket import send_request
import json
from datetime import datetime
import pytz
from pdf import generate_invoice
from utils import clear_terminal, print_colored_message, update_sense_hat, get_scooter, if_booked, calculate_total_time, get_time

scooter_id = 0

def login_display():
    """Display login prompt and handle user input."""
    username = input("Username: ")
    password = input("Password: ")
    response = send_request(f"LOGIN|{username}|{password}")
    status = response.split("|")[0]

    if status == "SUCCESS":
        user = json.loads(response.split("|")[1])
        clear_terminal()
        print_colored_message("Login successful!", "green", True)
        return user["id"], user["username"]
    elif status == "FAILURE":
        clear_terminal()
        print_colored_message("Incorrect password or email", "red", True)
        return "Fail", None


def scooter_display(name,scooter_data):
    """Display scooter data in a table."""
    print(f"\nHello {colored(name.capitalize(), 'green', attrs=['bold'])}, you already booked this scooter:")

    if not scooter_data:
        print_colored_message("No scooters available. Please login again.", "red")
        return None

    # Create PrettyTable and set column names
    table = PrettyTable()
    table.field_names = [colored("Name", attrs=["bold"]),
                         colored("Color", attrs=["bold"]),
                         colored("Cost/Hour", attrs=["bold"]), colored("Status", attrs=["bold"])]
    
    # Add rows to the table
    row = [ 
        scooter_data["make"], 
        scooter_data["color"],
        scooter_data["cost_per_minute"], 
        scooter_data["status"]
    ]
    table.add_row(row)
    
    # Print the table with color customization
    print(str(table).replace("+", colored("+", "blue"))
                          .replace("-", colored("-", "blue"))
                          .replace("|", colored("|", "blue"))
                          .replace("Name", colored("Name", "yellow", attrs=["bold"]))
                          .replace("Color", colored("Color", "yellow", attrs=["bold"]))
                          .replace("Cost/Hour", colored("Cost/Hour", "yellow", attrs=["bold"]))
                          .replace("Status", colored("Status", "yellow", attrs=["bold"]))
                          .replace("waiting", colored("Waiting", "blue"))
                          .replace("inuse", colored("InUse", "green")))

def display_option(scooter):
    """Display options based on scooter status."""
    options = {
        "waiting": ("You want to check in this scooter (Yes/Return): ", "checkin"),
        "in_use": ("You want to check out and pay for this scooter (Yes/Return): ", "checkout")
    }

    input_string, action = options.get(scooter["status"], ("Invalid status", ""))
    while True:
        choice = input(input_string)
        if choice == "Yes":
            return action, choice
        elif choice == "Return":
            return action, choice
        else:
            print_colored_message("Invalid option, please choose again", "red", True)

def generate_bill(scooter ,booking, checkout_time):

    total_time_used = calculate_total_time(booking["checkin_time"], checkout_time)
    total_price = scooter["cost_per_minute"] * total_time_used
    
    checking_date = booking["checkin_time"].split(" ")[0]
    checking_time = booking["checkin_time"].split(" ")[1]

    checkout_date = checkout_time.split(" ")[0]
    checkout_time = checkout_time.split(" ")[1] 

    print(colored("\nBILL","yellow", attrs=["bold"]))
    print(f"Checkin time: {checking_date} at {checking_time}")
    print(f"Checkout time: {checkout_date} at {checkout_time}")
    print(f"Time used: {total_time_used} hours")
    print(f"Cost per hour: {scooter['cost_per_minute']}/hour")
    print("-----------------------------------")
    print(colored(f"Total price: {total_price}", attrs=["bold"]))

    return total_time_used, total_price

def handle_check_in(booking):
    formatted_time = get_time()

    elier_checking = calculate_total_time(booking["rent_date"], formatted_time)
    if elier_checking < 0:
        checkin = input("Do you want to check in early (Yes/No): ")
        if checkin == "Yes":
            checkin_scooter(booking["id"], formatted_time)
        else:
            print("You chose to wait.")
    else:
        unlock = input("Do you want to unlock the scooter (Yes/No): ")
        if unlock == "Yes":
            checkin_scooter(booking["id"], formatted_time)
        else:
            print("You chose to wait.")
            return "Fail"

def handle_check_out(scooter ,total_time ,booking, formatted_time):
    print("Confirm (Yes/No): ")
    checkout = input()
    if checkout == "Yes":
        total_time_used = calculate_total_time(booking["checkin_time"], formatted_time)
        checkout_scooter(booking["id"], formatted_time, total_time * scooter["cost_per_minute"], scooter, booking, total_time_used)
    else:
        print("You chose to wait.")
        return "Fail"

def checkin_scooter(id, formatted_time):
    try:
        response = send_request(f"CHECKIN_BOOKING|{id}|{formatted_time}")
        status = response.split("|")[0]
        if status == "SUCCESS":
            print_colored_message("Scooter checked in successfully!", "green", True)
        else:
            print_colored_message("Failed to check in the scooter.", "red", True)

    except Exception as e:
        print_colored_message(f"Error checking in scooter: {e}", "red", True)
        return "Fail"
    return "Success"
    pass

def ask_to_generate_invoice(scooter, booking, formatted_time, total_time, total_price):

    request = input("Do you want to generate an invoice (Yes/No): ")
    if request == "Yes":
        print("Generating invoice...")
        generate_invoice(scooter, formatted_time, booking, total_price, total_time, "./webpage/static/logo.png", "./webpage/static/rmit.png")

def checkout_scooter(id, formatted_time, total_price, scooter, booking, total_time):
    try:
        response = send_request(f"CHECKOUT_BOOKING|{id}|{formatted_time}|{total_price}")
        status = response.split("|")[0]
        if status == "SUCCESS":
            print_colored_message("Scooter checked out successfully!", "green", True)
            ask_to_generate_invoice(scooter, booking, formatted_time, total_time, total_price)
        else:
            print_colored_message("Failed to check out the scooter.", "red", True)

    except Exception as e:
        print_colored_message(f"Error checking out scooter: {e}", "red", True)
        return "Fail"
    return "Success"

# Main application loop
def login_with_credentials(scooter):
    scooter_id = scooter
    
    clear_terminal()

    scooter_data = get_scooter(scooter_id)

    print("Welcome to the login page!")
    print("Please enter your credentials.")

    while True:
        auth, name = login_display()
        if auth != "Fail":
            break

    booked_status, booking = if_booked(auth, scooter_data)

    if booked_status == "BOOKED":
        scooter_display(name, scooter_data)
        if booking["status"] == "waiting":
            handle_check_in(booking)
        elif booking["status"] == "in_use":
            formatted_time = get_time()
            total_time, total_price = generate_bill(scooter_data,booking, formatted_time)
            handle_check_out(scooter_data, total_time ,booking, formatted_time)
            
    else :
        print_colored_message("You have not booked this scooter.", "red", True)
        print_colored_message("You can book this scooter at: http://127.0.0.1:5001.", "blue", True)
        exit()
    

    