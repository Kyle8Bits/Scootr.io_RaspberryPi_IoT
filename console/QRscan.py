from utils import clear_terminal, print_colored_message, get_time, calculate_total_time
from send_socket import send_request
import qrcode
from utils import get_scooter
import numpy as np
import cv2
from PIL import Image
import json
import threading
import time

def show_qr_code_window(image, stop_event):
    cv2.imshow("QR Code", image)
    while not stop_event.is_set():
        if cv2.waitKey(100) & 0xFF == 27:  # ESC key to close early (optional)
            stop_event.set()
            break
    cv2.destroyAllWindows()

def poll_server_for_scan_done(stop_event):
    while not stop_event.is_set():
        # Replace this command with your actual server check for scan done status
        response = send_request(f"CHECK_SCAN_STATUS")

        if response.strip() == "SCAN_DONE|NOT_BOOKED":
            print_colored_message("You have not booked this scooter. Please press 'R' to return.", "blue", True)
            stop_event.set()
            break
        if response.strip() == "SCAN_DONE|CHECKIN":
            print_colored_message("Checking in success. Please press 'R' to return.", "blue", True)
            stop_event.set()
            break
        if response.strip() == "SCAN_DONE|CHECKOUT":
            print_colored_message("Check out sucess. Please press 'R' to return.", "blue", True)

            stop_event.set()
            break
        if response.strip() == "SCAN_DONE|INSUFFICIENT_BALANCE":
            print_colored_message("You do not have enough money. Please press 'R' to return.", "red", True)
            stop_event.set()
            break
        time.sleep(2)  # Poll every 2 seconds

def show_qr_code(scooter_id, action):
    data = f"{scooter_id}|{action}"
    qr_img = qrcode.make(data)
    qr_img = qr_img.convert('RGB')
    open_cv_image = np.array(qr_img)
    open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

    stop_event = threading.Event()

    # Thread to display QR code window
    t1 = threading.Thread(target=show_qr_code_window, args=(open_cv_image, stop_event))
    t1.start()

    # Thread to poll server for scan done status
    t2 = threading.Thread(target=poll_server_for_scan_done, args=(stop_event,))
    t2.start()

    # Optionally, keep your existing input for 'R' to return manually too
    while not stop_event.is_set():
        choice = input().strip().lower()
        if choice == 'r':
            stop_event.set()
            break
        else:
            print("Invalid input. Please press 'R' to return.")

    t1.join()
    t2.join()


def signal_master_pi(scooter_id):
    response = send_request(f"QR_LOGIN_REQUEST|{scooter_id}")
    action = response.split("|")[1]
    print_colored_message("Waiting for scan....", "green", True)
    return action

def qr_option(scooter_id):
    action = signal_master_pi(scooter_id)
    show_qr_code(scooter_id, action)

    scooter_data = get_scooter(scooter_id)
    
    