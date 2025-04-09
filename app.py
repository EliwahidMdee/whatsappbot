
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

sessions = {}

def save_to_sheet(data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Ngatuka Bookings").sheet1
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get('phone'),
        data.get('language'),
        data.get('service'),
        data.get('location'),
        data.get('date'),
        data.get('duration')
    ])

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")
    resp = MessagingResponse()
    msg = resp.message()
    user = sessions.get(from_number, {"step": 0})

    if user["step"] == 0:
        msg.body("Please choose your preferred language:")
        msg.button("English")
        msg.button("French")
        user["step"] = 1

    elif user["step"] == 1:
        user["language"] = incoming_msg
        msg.body("Welcome to *Ng'atuka Travel Agency*! Which service would you like to book?")
        services = ["Tours", "Tour Guide", "Private Driver", "Car Rental", "City Transfer", "Airport Transfer", "Taxi", "Delivery"]
        for service in services:
            msg.button(service)
        user["step"] = 2

    elif user["step"] == 2:
        user["service"] = incoming_msg
        msg.body(f"Great! Where exactly do you want to start your {user['service']}?")
        user["step"] = 3

    elif user["step"] == 3:
        user["location"] = incoming_msg
        msg.body("On which date do you want the service? (e.g. 2025-04-07)")
        user["step"] = 4

    elif user["step"] == 4:
        user["date"] = incoming_msg
        msg.body("How long will you need the service? (e.g. 3 hours, 2 days)")
        user["step"] = 5

    elif user["step"] == 5:
        user["duration"] = incoming_msg
        user["phone"] = from_number
        save_to_sheet(user)
        msg.body("Thanks! Your booking has been recorded. We’ll contact you shortly to confirm.")
        sessions.pop(from_number)

    sessions[from_number] = user
    return str(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=10000,debug=True)
