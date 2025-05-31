from credentials import login_with_credentials
from QRscan import qr_option
from utils import update_sense_hat, clear_terminal, clear_display
import sys
from engineer_scanner import enginner_scan_personal_qr_code


scooter_id = 0

if __name__ == "__main__":
    clear_display()
    update_sense_hat(scooter_id)
    
    if len(sys.argv) > 1:
        try:
            scooter_id = int(sys.argv[1])
        except ValueError:
            print("Invalid scooter ID provided. It must be a number.")
            exit(1)
    else:
        print("No scooter ID provided, using default ID (5).")
        scooter_id = 1  # Default scooter ID


    try:
        while(1):
            clear_terminal()

            print("Welcome! Please select login method:")
            print("1. Login with credentials")
            print("2. Login with QR code")
            print("3. Open scanner")
            choice = input("Enter choice (1 to 3): ")

            if choice == "1":
                login_with_credentials(scooter_id)
                update_sense_hat(scooter_id)
            elif choice == "2":
                qr_option(scooter_id)
                update_sense_hat(scooter_id)
            elif choice == "3":
                enginner_scan_personal_qr_code(scooter_id)
                update_sense_hat(scooter_id)

                
    except KeyboardInterrupt:
        print("\nExiting program...")
        clear_display()  # Call your cleanup function here
        sys.exit(0)