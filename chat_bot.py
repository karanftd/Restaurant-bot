from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import CommandHandler, Updater, MessageHandler, RegexHandler, ConversationHandler, Filters
from settings import *
from Booking import Booking

from google.cloud import datastore

import re
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)

# create datastore instance
datastore_client = datastore.Client(PROJECT_ID)

# Chatting states
BOOKING, CONFIRMATION, SENDEMAIL, GOODBYE = range(4)

# identify booking intention 
book = 'book'

# identify person
peopleIdentify = ['people', 'person', 'ppl']

bookings = {}



def start(bot, update):
    
    # get the user information
    user = update.message.from_user
    logger.info("User %s %s started the conversation.", user.first_name, user.id )
    bookobj = Booking()
    bookobj.user_id = user.id
    bookobj.name = user.first_name
    bookings[user.id] = bookobj

    #TODO : Greet user differently if User visit again (Based on user.id)
    update.message.reply_text('Hi Welcome to XYZ,\nHow would I help you today?')

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
        people = re.findall(r"(\d{0,2})?\s?(people|person|ppl)",message)

        if people and len(people) > 0:

            print people[0][0]
            bookobj.person = people[0][0]

        elif not bookobj.person:
            
            people = re.findall(r"(for)?\s?(\d)",message)
            print people
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

'''def choice_of_table(bot, update):
    
    # keyboard choice
    reply_keyboard = [['Yes', 'No']]
    user = update.message.from_user

    # TODO : Handling for No
    # Exit the chat if User selects No

    message = update.message.text
    bookobj = bookings[update.message.from_user.id]
    bookobj.table = message
    logger.info("%s selection of tables is %s ", user.first_name, update.message.text)

    update.message.reply_text('Would you like to book this?', 
                                reply_markup = ReplyKeyboardMarkup(reply_keyboard, 
                                one_time_keyboard=True))
    
    return CONFIRMATION
'''
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
    bookobj = bookings[user.id]
    bookobj.email = update.message.text

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
    update.message.reply_text(message)

    return ConversationHandler.END

def bye(bot, update):
    
    # send goodbye greetings
    user = update.message.from_user
    logger.info("Sending email to : %s", user.first_name)
    del bookings[user.id]
    update.message.reply_text('it was nice to talking with you %s.',user.first_name)

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
            
            #CHOOSETABLE: [RegexHandler('^(Beach View|Poolside|Air-Conditioned Hall|Other)$', choice_of_table)],

            CONFIRMATION: [MessageHandler(Filters.text, confirmation)],

            SENDEMAIL: [MessageHandler(Filters.text, send_email)],

            GOODBYE : [MessageHandler(Filters.text, bye)],

        },

        fallbacks = [RegexHandler('^(cancle|bye)$', bye)]
    )
    dp.add_handler(conv_handler)

    # in case of any error
    dp.add_error_handler(error)

    updater.start_polling()
    #bot will run untll you press Ctrl-C
    print "press Ctrl-C for exit \nBot is listening.."

    updater.idle()



if __name__ == '__main__':
    main()
