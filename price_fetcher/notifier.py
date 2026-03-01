import os
import smtplib
import warnings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import configparser
from dotenv import load_dotenv

load_dotenv()

config = configparser.ConfigParser()
config.read("config.ini")

# Load dates from config to identify departure and return flight
dep_date = config["dates"]["dep_date"]
ret_date = config["dates"]["ret_date"]

# Configure gmail smtp connection
host = "smtp.gmail.com"
port = 587 
outgoing_mail = os.getenv("SMTP_MAIL")
password = os.getenv("SMTP_PASSWORD")
alert_mail = config["settings"]["alert_mail"]


def build_email(stats: list[dict]):
    """
    Build the email from a list of route summary statistics.

    :param stats: List of stats dicts for each route
    :return: text string with route price information
    """
    # Separate sections for departure and return flights
    dep_lines = [f"\nDeparture Flight ({dep_date})", "-" * 50]
    ret_lines = [f"\nReturn Flight ({ret_date})", "-" * 50]

    # Loop over each route
    for s in stats:
        # Text used for all routes
        text_lines = [
            f"  Current price:  {s['current_price']:.2f}",
            f"  Last price:     {s['last_price']:.2f}",
            f"  All-time low:   {s['all_time_low']:.2f}",
            f"  All-time high:  {s['all_time_high']:.2f}",
            f"  30-day low:     {s['low_30d']:.2f}",
            f"  30-day high:    {s['high_30d']:.2f}",
        ]

        # Build departure flight text block
        if s["date"] == dep_date:
            dep_lines.append(f"\n{s['origin']} → {s['destination']} ({s['unit']})")
            dep_lines.extend(text_lines)
        # Build return flight text block
        if s["date"] == ret_date:
            ret_lines.append(f"\n{s['origin']} → {s['destination']} ({s['unit']})")
            ret_lines.extend(text_lines)

    # Append the return section after the departure section
    dep_lines.extend(ret_lines)
    return "\n".join(dep_lines)


async def send_email(stats: list[dict]):
    """
    Build and send price summary email via Gmail

    :param stats: List of stats dicts as returned by fetch_and_store_price
    """
    body = build_email(stats)

    # Setup email 
    msg = MIMEMultipart()
    msg["From"] = outgoing_mail
    msg["To"] = alert_mail
    msg["Subject"] = "Flight Price Update"
    msg.attach(MIMEText(body, "plain"))

    # try sending mail else print an error
    try:
        with smtplib.SMTP(host, port) as server:
            server.ehlo()        
            server.starttls()    
            server.login(outgoing_mail, password)
            server.sendmail(outgoing_mail, alert_mail, msg.as_string())
            print(f"Email sent to {alert_mail}")
    except Exception as e:
        warnings.warn(f"Failed to send email: {e}")
