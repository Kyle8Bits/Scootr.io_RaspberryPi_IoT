"""
client_handle.py

Client communication handler module for the scooter management system.

This module receives client requests over a TCP socket, processes commands
related to user management, scooter management, and booking operations,
and sends appropriate responses back to the client.

Functions:
- send_data_to_client: Sends encoded data to a client socket.
- handle_client: Receives client requests, parses commands, dispatches them to the appropriate service functions, and returns responses.
"""

import json
import socket
from ..service.UserService import User
from ..service.ScooterService import Scooter
from ..service.BookingService import Booking
from ..service.ReportService import Report
from ..service.AdminService import Admin
from ..service.EngineerService import Engineer


qr_response = None  # module-level global variable
qr_scan_state = 0  # module-level global variable

def send_data_to_client(client_socket, data):
    """
    Send encoded data to a client over the socket in chunks (handling data larger than 4096 bytes).

    Args:
        client_socket (socket.socket): The client socket to send data to.
        data (str): The string data to be sent.
    """
    try:
        # Convert data to bytes
        byte_data = data.encode('utf-8')
        # Send data in chunks of 4096 bytes
        chunk_size = 8192
        total_sent = 0
        while total_sent < len(byte_data):
            sent = client_socket.send(byte_data[total_sent:total_sent+chunk_size])
            total_sent += sent
    except socket.error as e:
        print(f"❌ Error sending data to client: {e}")

def handle_client(client_socket):
    global qr_scan_state
    global qr_response
    """
    Handle incoming client requests.

    Receives the request string, parses the command and arguments,
    routes the request to the correct service function, and sends
    back the appropriate response.

    Args:
        client_socket (socket.socket): The socket representing the client connection.
    """
    try:
        request = client_socket.recv(4096).decode('utf-8')
        data_array = request.strip().split('|')
        command = data_array[0]
        # if(command != "CHECK_SCAN_STATUS"):
        print(f"📩 Received request: {data_array}")


        # DONE
        if command == "LOGIN" and len(data_array) >= 3:
            print(f"Checking if user exists with username: {data_array[1]} and email: {data_array[2]}")
            send_data_to_client(client_socket, User.login(data_array[1], data_array[2]))

        elif command == "GET_USER_ID_BY_EMAIL" and len(data_array) >= 2:
            email = data_array[1]
            response = User.get_user_id_by_email(email)
            send_data_to_client(client_socket, response)

        elif command == "IF_EXIST" and len(data_array) >= 3:
            send_data_to_client(client_socket, User.if_exist(data_array[1], data_array[2]))

        elif command == "REGISTER" and len(data_array) >= 4:
            print(f"Registering user with username: {data_array[1]} and email: {data_array[2]}")
            send_data_to_client(client_socket, User.register(data_array[1], data_array[2], data_array[3]))

        elif command == "GET_ALL_SCOOTER":
            send_data_to_client(client_socket, Scooter.get_all_scooter())

        elif command == "BOOK_THE_SCOOTER" and len(data_array) >= 5:
            send_data_to_client(client_socket, Booking.create_booking(data_array[1], data_array[2], data_array[3], data_array[4]))

        elif command == "GET_USER_PROFILE" and len(data_array) >= 2:
            send_data_to_client(client_socket, User.get_user_profile(data_array[1]))
        #DONE
            
        elif command == "GET_SCOOTER_BY_ID" and len(data_array) >= 2:
            send_data_to_client(client_socket, Scooter.get_scooter_by_id(data_array[1]))

        #DONE
        elif command == "GET_SCOOTER_DETAILS" and len(data_array) >= 2:
            send_data_to_client(client_socket, Scooter.get_scooter_details(data_array[1]))

        elif command == "UPDATE_USER_INFO" and len(data_array) >= 3:
            send_data_to_client(client_socket, User.update_info(data_array[1], data_array[2]))

        elif command == "CHANGE_PASSWORD" and len(data_array) >= 3:
            send_data_to_client(client_socket, User.change_password(data_array[1], data_array[2]))

        elif command == "TOP_UP" and len(data_array) >= 3:
            user_id = int(data_array[1])
            amount = int(data_array[2])
            send_data_to_client(client_socket, User.top_up(user_id, amount))

        elif command == "HISTORY" and len(data_array) >= 2:
            send_data_to_client(client_socket, User.get_booking_history(data_array[1]))

        elif command == "CANCEL_BOOKING" and len(data_array) >= 3:
            send_data_to_client(client_socket, Booking.cancel_booking(data_array[1], data_array[2]))
            
        elif command == "GET_ALL_TOPUPS":
            send_data_to_client(client_socket, User.get_all_topups())

        elif command == "GET_ALL_APPROVE_ISSUES_DETAILS":
            send_data_to_client(client_socket, Engineer.get_all_approve_issues_details())
            
        elif command == "CHECKIN_BOOKING" and len(data_array) == 3:
            booking_id = int(data_array[1])
            checkin_datetime = data_array[2]

            result = Booking.checkin_booking(booking_id, checkin_datetime)

            send_data_to_client(client_socket, result)

        elif command == "CHECKOUT_BOOKING" and len(data_array) >= 4:
            send_data_to_client(client_socket, Booking.checkout_booking(data_array[1], data_array[2], data_array[3]))

        elif command == "REPORT_ISSUE" and len(data_array) >= 7:
            send_data_to_client(client_socket, Report.report_issue(data_array[1], data_array[2], data_array[3], data_array[4], data_array[5], data_array[6]))
        elif command == "GET_BY_ID" and len(data_array) >= 2:
            send_data_to_client(client_socket, User.get_by_id(data_array[1]))

        elif command == "GET_ALL_USERS" and len(data_array) == 2:
            role = data_array[1]  # could be 'customer','engineer', or 'ALL'
            send_data_to_client(client_socket,
                User.get_all_users(role)
            )
        elif command == "GET_USER_REPORT_COUNT" and len(data_array) == 2:
            send_data_to_client(client_socket, Report.get_report_count(data_array[1]))

        elif command == "GET_USER_BOOKING_COUNT" and len(data_array) == 2:
            send_data_to_client(client_socket, Booking.get_user_booking_count(data_array[1]))

        elif command == "GET_USAGE_HISTORY":
            send_data_to_client(client_socket, Booking.get_usage_history())


        elif command == "GET_USER_DETAILS" and len(data_array) == 2:
            send_data_to_client(client_socket,
                User.get_user_details(int(data_array[1]))
            )

        elif command == "ADD_USER" and len(data_array) >= 5:
            # expects: ADD_USER|role|username|email|password[|first_name][|last_name][|phone_number]
            role       = data_array[1]
            username   = data_array[2]
            email      = data_array[3]
            password   = data_array[4]
            first_name   = data_array[5] if len(data_array) > 5 else None
            last_name    = data_array[6] if len(data_array) > 6 else None
            phone_number = data_array[7] if len(data_array) > 7 else None

            send_data_to_client(client_socket,
                User.add_user(role, username, email, password,
                              first_name, last_name, phone_number)
            )

        elif command == "EDIT_USER" and len(data_array) == 3:
            # expects: EDIT_USER|user_id|data_json
            user_id   = int(data_array[1])
            data_json = data_array[2]
            send_data_to_client(client_socket,
                User.edit_user(user_id, data_json)
            )

        elif command == "DELETE_USER" and len(data_array) == 2:
            send_data_to_client(client_socket,
                User.delete_user(int(data_array[1]))
            )

        elif command == "GET_ALL_ISSUES":
            send_data_to_client(client_socket, Report.get_all_issues())

        elif command == "RESOLVE_ISSUE" and len(data_array) >= 2:
            issue_id = int(data_array[1])
            send_data_to_client(client_socket, Report.mark_as_resolved(issue_id))

        elif command == "GET_ALL_ZONES":
            # calls Scooter.get_all_zones(), which returns "SUCCESS|[...zones json...]"
            send_data_to_client(client_socket, Scooter.get_all_zones())

        elif command == "GET_ALL_BOOKINGS":
            send_data_to_client(client_socket, Booking.get_all_bookings())
        elif command == "ADD_SCOOTER" and len(data_array) >= 7:
            send_data_to_client(client_socket, Scooter.add_scooter(*data_array[1:7]))

        elif command == "EDIT_SCOOTER" and len(data_array) >= 8:
            send_data_to_client(client_socket, Scooter.edit_scooter(*data_array[1:8]))

        elif command == "GET_ENGINEER_ISSUES" and len(data_array) == 2:
            engineer_id = int(data_array[1])
            send_data_to_client(client_socket, Engineer.get_issues_assigned_to_engineer(engineer_id))
            
        elif command == "ENGINEER_MARK_RESOLVED" and len(data_array) >= 5:
            issue_id = int(data_array[1])
            engineer_id = int(data_array[2])
            resolution_type = data_array[3]
            resolution_details = data_array[4]
            result = Engineer.mark_resolved(issue_id, engineer_id, resolution_type, resolution_details)
            send_data_to_client(client_socket, result)

        elif command == "GET_ENGINEER_RESOLVED_ISSUES" and len(data_array) == 2:
            engineer_id = int(data_array[1])
            result = Engineer.get_resolved_issues(engineer_id)
            send_data_to_client(client_socket, result)

        elif command == "DELETE_SCOOTER" and len(data_array) >= 2:
            send_data_to_client(client_socket, Scooter.delete_scooter(data_array[1]))

        elif command == "GET_ISSUE_BY_ID" and len(data_array) >= 2:
            response = Report.get_issue_by_id(int(data_array[1]))
            send_data_to_client(client_socket, response)
        elif command == "GET_TOP_SCOOTERS":
            send_data_to_client(client_socket, Booking.get_top_scooters())

        elif command == "APPROVE_ISSUE" and len(data_array) >= 2:
            issue_id = data_array[1]
            send_data_to_client(client_socket, Admin.approve_issue(issue_id))
            
        elif command == "GET_ALL_ENGINEERS_EMAIL":
            result = Admin.get_all_engineers_email()
            send_data_to_client(client_socket, result)

        elif command == "GET_ANALYTICS" and len(data_array) == 2:
            mode = data_array[1].lower()  # daily or weekly
            send_data_to_client(client_socket, Booking.get_usage_analytics(mode))
             
        elif command == "ENGINEER_CLAIM_ISSUE" and len(data_array) >= 3:
            issue_id = data_array[1]
            user_id = data_array[2]
            send_data_to_client(client_socket, Engineer.engineer_claim_issue(issue_id, user_id))
            
        elif command == "GET_INVOICE" and len(data_array) >= 2:
            send_data_to_client(client_socket, Booking.get_invoice(data_array[1]))
        
        elif command == "QR_LOGIN_REQUEST" and len(data_array) >= 2:
            scooter_id = data_array[1]
            qr_scan_state = 1 
            send_data_to_client(client_socket, User.checking_qr(scooter_id))

        elif command == "QR_LOGIN_SCAN" and len(data_array) >= 4:
            scooter_id = int(data_array[1])
            action = data_array[2]
            username = data_array[3]
            qr_scan_state = 2
            qr_response = User.qr_proccess(scooter_id, username, action)
            send_data_to_client(client_socket, qr_response)

        elif command == "CHECK_SCAN_STATUS" and len(data_array) >= 1:
            state = qr_scan_state
            if state == 2:
                if qr_response == "NOT_BOOKED":
                    send_data_to_client(client_socket, "SCAN_DONE|NOT_BOOKED")
                elif qr_response == "SUCCESS_CHECK_IN":
                    send_data_to_client(client_socket, "SCAN_DONE|CHECKIN")
                elif qr_response == "SUCCESS_CHECK_OUT":
                    send_data_to_client(client_socket, "SCAN_DONE|CHECKOUT")
                elif qr_response == "INSUFFICIENT_BALANCE":
                    send_data_to_client(client_socket, "SCAN_DONE|INSUFFICIENT_BALANCE")
            else:
                send_data_to_client(client_socket, "PENDING")

        elif command == "ADD_COMMENT" and len(data_array) >= 4:
            username = data_array[1]
            scooter_id = data_array[2]
            comment = data_array[3]
            send_data_to_client(client_socket, User.create_comment(username, scooter_id, comment))

        elif command == "ENGINEER_SCAN" and len(data_array) >= 3:
            engineer_id= int(data_array[1])
            scooter_id = int(data_array[2])
            send_data_to_client(client_socket, Engineer.handle_engineer_scan(engineer_id, scooter_id))


        else:
            send_data_to_client(client_socket, "ERROR|Unknown or malformed command")

    except socket.error as e:
        print(f"❌ Socket error while handling client: {e}")
        send_data_to_client(client_socket, "ERROR|Socket error")

    except Exception as e:
        print(f"❌ General error while handling client: {e}")
        send_data_to_client(client_socket, "ERROR|Server failure")

    finally:
        client_socket.close()
