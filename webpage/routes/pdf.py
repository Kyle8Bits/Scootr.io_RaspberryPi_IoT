from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import os

class InvoicePDF(FPDF):
    def header(self):
        self.set_fill_color(56, 73, 129)
        self.rect(0, 0, 210, 30, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", 'B', 18)
        self.set_y(10)
        self.cell(0, 10, "Scootr.io - Rental Invoice", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Helvetica", '', 8)
        self.set_text_color(120, 120, 120)
        self.ln(3)
        self.cell(0, 5, "IoT Programming - RMIT University Vietnam", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 5, "Developed by: Mai Dang Khoa | Shirin Shujaa | Trinh Phuong Thao", align='C')

def generate_invoice(scooter, checkout_time, booking, total_price,logo_left, logo_right):
    rate = scooter["cost_per_minute"]

    pdf = InvoicePDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    if os.path.exists(logo_left):
        pdf.image(logo_left, x=15, y=35, w=25)
    if os.path.exists(logo_right):
        pdf.image(logo_right, x=170, y=35, w=25)

    pdf.ln(48)

    # Section card with accent left bar
    y_start = pdf.get_y()
    card_height = 95
    pdf.set_fill_color(88, 129, 242)
    pdf.rect(10, y_start, 3, card_height, 'F')

    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(10, y_start, 190, card_height, style='DF')

    pdf.set_y(y_start + 6)
    pdf.set_font("Helvetica", 'B', 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Scooter: {scooter['make']} (ID: {scooter['id']})", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    checking_date = booking['checkin_time'].split(" ")[0]
    checking_time = booking['checkin_time'].split(" ")[1]

    checkout_time_only = checkout_time.split(" ")[1]
    checkout_date = checkout_time.split(" ")[0]
    # Booking info


    rows = [
        ("Check-in", f"{checking_date} at {checking_time}"),
        ("Checkout", f"{checkout_date} at {checkout_time_only}"),
        ("Time Used", f"{calculate_total_time(booking['checkin_time'], checkout_time[:16])} hours"),
        ("Rate", f"${rate:.2f}/hour"),
        ("Total", f"${total_price:,.2f}")
    ]

    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(95, 10, "Detail", border=1, align='C', fill=True)
    pdf.cell(95, 10, "Information", border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", '', 11)
    for i, (label, val) in enumerate(rows):
        pdf.set_fill_color(245, 245, 245) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.cell(95, 10, label, border=1, fill=True)
        align = 'R' if any(c in val for c in "$0123456789hm") else 'L'
        pdf.cell(95, 10, val, border=1, align=align, fill=True)
        pdf.ln()

    # Bottom thank you
    pdf.ln(10)
    pdf.set_font("Helvetica", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Thank you for using Scootr.io!", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    # Save
    path = os.path.join(os.path.expanduser("~"), "Downloads", f"scooter_invoice_{checkout_date}.pdf")
    pdf.output(path)
    print(f"✅ PDF saved to {path}")


def calculate_total_time(time_import, time_now):
    total_hours = 1
    # Parse the date-time strings into datetime objects
    time_import = datetime.strptime(time_import, "%Y-%m-%d %H:%M:%S")
    time_now = datetime.strptime(time_now, "%Y-%m-%d %H:%M")
    
    # Calculate the difference in days
    days_difference = (time_now - time_import).days

    # Calculate the total difference in minutes for the time portion
    total_minutes_now = time_now.hour * 60 + time_now.minute
    total_minutes_import = time_import.hour * 60 + time_import.minute

    # Calculate the total time in minutes for the time difference
    total_time_in_minutes = total_minutes_now - total_minutes_import

    # Convert the total time into hours and handle any remaining minutes
    total_hours = total_time_in_minutes // 60  # This gives the full hours
    remaining_minutes = total_time_in_minutes % 60  # This gives the remaining minutes

    # If there are any remaining minutes greater than 10, round up the hour
    if remaining_minutes > 10:
        total_hours += 1
    
    # Add the day difference in hours to the total hours
    total_hours += (days_difference * 24)

    print(f"Total hours {total_hours} hours")
    
    return total_hours