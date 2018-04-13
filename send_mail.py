import sendgrid
import os
from settings import *
from sendgrid.helpers.mail import *
from Booking import Booking



def sendMail(booking):
    
    sg = sendgrid.SendGridAPIClient(apikey=SENDGRIDKEY)
    from_email = Email("no-reply@jumper.com")
    print booking
    to_email = Email(booking.email)
    subject = "Your Reservation Confirmed"
    body = "Hello {}, We have book a table for {} ({}) at {}".format(booking.name, booking.person, booking.table, booking.time)
    content = Content("text/plain", body)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    