from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import CommandHandler, Updater, MessageHandler, RegexHandler, ConversationHandler, Filters
from settings import *
from Booking import Booking
from send_mail import sendMail

from google.cloud import datastore

import re
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)

# create datastore instance
datastore_client = datastore.Client(PROJECT_ID)

# Chatting states
BOOKING, CHOICE, CONFIRMATION, SENDEMAIL, GOODBYE = range(5)

# identify booking intention 
book = 'book'

# identify person
peopleIdentify = ['people', 'person', 'ppl']

# store user booking information 
bookings = {}

def start(bot, update):
    
    # get the user information
    user = update.message.from_user
    logger.info("User %s %s started the conversation.", user.first_name, user.id )

    #TODO : Greet user differently if User visit again (Based on user.id)
    query = datastore_client.query(kind='user')
    query.add_filter('id', '=', user.id)
    results = list(query.fetch())
    bookobj = Booking()
    if len(results) > 0:
        
        # User already exist in our database
        bookobj.name = results[0]['name']
        bookobj.user_id = results[0]['id']
        bookobj.person = results[0]['members']
        bookobj.table = results[0]['last_choice']
        bookobj.email = results[0]['email']
        bookobj.time = results[0]['time']
        bookings[user.id] = bookobj

        # keyboard choice
        reply_keyboard = [['Yes', 'No']]

        update.message.reply_text('Hi Welcome back {}! Would you like to book table same as last time? Table for {}-{} at {}'.format(bookobj.name,
                                    bookobj.person, bookobj.table, bookobj.time), 
                                    reply_markup = ReplyKeyboardMarkup(reply_keyboard, 
                                    one_time_keyboard=True))

        return CHOICE

    else:
    
        # update user information in Booking
        bookobj.user_id = user.id
        bookobj.name = user.first_name
        bookings[user.id] = bookobj

        # Greet user
        update.message.reply_text('Hi Welcome to XYZ,\nHow would I help you today?')

        return BOOKING

def choice(bot, update):
    
    # get user information from User
    user = update.message.from_user
    # get message from user
    message = update.message.text
    bookobj = bookings[update.message.from_user.id]
    if message.lower() == 'yes':
        
        message = 'Thank you {}! Your booking is confirmed, table for {}, {} at {} '.format(
                                    bookobj.name, bookobj.person, bookobj.table, bookobj.time)
        
        update.message.reply_text(message)
        
        # send email confirmation
        sendMail(bookobj)

        return ConversationHandler.END

    else:
        # Continue with bookings
        logger.info("Recieved confirmation from user %s : %s", user.first_name, update.message.text)
        bookobj = bookings[update.message.from_user.id]
        bookobj.person = None
        bookobj.table = None
        bookobj.email = None
        bookobj.time = None
        bookings[update.message.from_user.id] = bookobj
        update.message.reply_text('How may I help you today?')
        
        return BOOKING

def booking(bot, update):
    
    # choice of sitting arrangement 
    reply_keyboard = [['Beach View', 'Poolside', 'Air-Conditioned Hall', 'Other']]

    # get the user information 
    message = update.message.text
    print message

    bookobj = bookings[update.message.from_user.id]
    # check if we got already person data
    if bookobj is not None and bookobj.person is None:
        
        # get the person information from chat message
        # check the pattern like '2 people/ppl/person'
        people = re.findall(r"(\d{0,2})?\s?(people|person|ppl)",message)

        # check if we found people information
        if people and len(people) > 0:

            bookobj.person = people[0][0]

        # check for the pattern 'for n' people
        elif not bookobj.person:
            
            people = re.findall(r"(for)?\s?(\d)",message)
            
            if people:
                bookobj.person = people[0][1]

        else:
            reply = 'For how many people? (ie. for 2 People, 4 ppl or 3 person)' 
            logger.info("unable to get people information from message")
            update.message.reply_text(reply)
            return BOOKING
    
    if bookobj is not None and bookobj.time is None:
        time = re.findall(r"(\d{0,2}:\d{0,2})?\s?(am|pm|AM|PM|today|tonight)",message)

        if time and len(time) > 0:
            
            bookobj.time = time[0][0]
        else:
    
            time = re.findall(r"(at)\s?(\d)|(\d{0,2}:\d{0,2})",message)
            if bookobj.time:
                bookobj.time = time[0][1]
            
            # suggest user about how he should type request
            reply = 'For what time? (ie. 9:00 PM, 9:30 tonight, 11:30 am)'
            logger.info("unable to get time information from message")
            update.message.reply_text(reply)
            return BOOKING
    
    #logger.info("booking initiated by %s and recived message %s", user.first_name, update.message.text)

    logger.info("suggesting choice of tables.")

    update.message.reply_text('Sure! Do you have any sitting preferences?', 
                                reply_markup = ReplyKeyboardMarkup(reply_keyboard, 
                                one_time_keyboard=True))
    
    return CONFIRMATION

def confirmation(bot, update):
    
    # get user information from User
    user = update.message.from_user
    bookobj = bookings[user.id]
    message = update.message.text
    bookobj.table = message
    logger.info("Recieved confirmation from user %s : %s", user.first_name, update.message.text)

    update.message.reply_text('Please share your email, we will send you confirmation.')
    
    return SENDEMAIL

def send_email(bot,update):
    
    # send email to user
    user = update.message.from_user
    email = update.message.text
    # TODO : Validate Email
    if not validate_email(email):
        
        update.message.reply_text('Please share valid email address.')
        return SENDEMAIL
        
    bookobj = bookings[user.id]
    bookobj.email = email

    logger.info("Recieved confirmation from user %s : %s", user.first_name, update.message.text)
    
    kind = 'user'
    user_id = bookobj.user_id

    print user_id
    
    add_user = datastore_client.key(kind,user_id)

    task = datastore.Entity(key= add_user)

    #task['chat_id'] = bookobj.user_id
    task['email'] = bookobj.email
    task['id'] = bookobj.user_id
    task['last_choice'] = bookobj.table
    task['members'] = bookobj.person
    task['name'] = bookobj.name
    task['time'] = bookobj.time

    datastore_client.put(task)

    #booking.put()

    message = 'Thank you {}! Your booking is confirmed, table for {}, {} at {} '.format(
                                    bookobj.name, bookobj.person, bookobj.table, bookobj.time)

    # TODO : Send Email to User 
    sendMail(bookobj)
    update.message.reply_text(message)

    return ConversationHandler.END

def bye(bot, update):
    
    # send goodbye greetings
    user = update.message.from_user
    logger.info("Sending email to : %s", user.first_name)
    del bookings[user.id]
    update.message.reply_text('it was nice to talking with you %s.',user.first_name)

    return ConversationHandler.END

def exitchat(bot, update):
    """ gracefully exit chat """
    logger.warning('Unable to read message from user exiting current chat')

    update.message.reply_text('Sorry %s, unable to understand your message exiting chat. Startover chat again by typing ''\start'.formate(user.first_name))

    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():

    # create event handler
    updater = Updater(TOKEN)

    # get the dispacher to register handlers
    dp = updater.dispatcher
    
    # conversation states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states = {

            BOOKING : [MessageHandler(Filters.text, booking)],

            CHOICE : [MessageHandler(Filters.text, choice)],
            
            CONFIRMATION: [MessageHandler(Filters.text, confirmation)],

            SENDEMAIL: [MessageHandler(Filters.text, send_email)],

            GOODBYE : [MessageHandler(Filters.text, bye)],

        },

        fallbacks = [RegexHandler('^(cancle|bye)$', bye)]
    )
    dp.add_handler(conv_handler)

    # in case of any error
    dp.add_error_handler(error)

    #bot will run untll you press Ctrl-C
    updater.start_polling()
    print "press Ctrl-C for exit \nBot is listening.."

    updater.idle()



if __name__ == '__main__':
    main()
