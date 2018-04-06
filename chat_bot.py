from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import CommandHandler, Updater, MessageHandler, RegexHandler, ConversationHandler, Filters
from settings import *

import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)

# Chatting states
BOOKING, CHOOSETABLE, CONFIRMATION, SENDEMAIL, GOODBYE = range(5)

def start(bot, update):
    
    # get the user information
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)

    #TODO : Greet user differently if User visit again (Based on user.id)
    update.message.reply_text('Hi Welcome to XYZ,\nHow would I help you today?')

    return BOOKING

def booking(bot, update):
    
    # choice of sitting arrangement 
    reply_keyboard = [['Beach View', 'Poolside', 'Air-Conditioned Hall', 'Other']]

    # get the user information 
    user = update.message.from_user

    # TODO : update.message.text Parse user Message and derive table booking data
    
    logger.info("booking initiated by %s and recived message %s", user.first_name, update.message.text)

    logger.info("suggesting choice of tables.")

    update.message.reply_text('Sure! Do you have any sitting preferences?', 
                                reply_markup = ReplyKeyboardMarkup(reply_keyboard, 
                                one_time_keyboard=True))
    
    return CHOOSETABLE

def choice_of_table(bot, update):
    
    # keyboard choice
    reply_keyboard = [['Yes', 'No']]

    # TODO : Handling for No
    # Exit the chat if User selects No

    user = update.message.from_user
    logger.info("%s selection of tables is %s ", user.first_name, update.message.text)

    update.message.reply_text('Would you like to book this?', 
                                reply_markup = ReplyKeyboardMarkup(reply_keyboard, 
                                one_time_keyboard=True))
    
    return CONFIRMATION

def confirmation(bot, update):
    
    # get user information from User
    user = update.message.from_user
    logger.info("Recieved confirmation from user %s : %s", user.first_name, update.message.text)

    update.message.reply_text('Please share your email, we will send you confirmation.')
    
    return SENDEMAIL

def send_email(bot,update):
    
    # send email to user
    user = update.message.from_user
    # TODO : Validate Email
    logger.info("Recieved confirmation from user %s : %s", user.first_name, update.message.text)
    # TODO : Send Email to User 
    update.message.reply_text('Thank you!')

    return GOODBYE

def bye(bot, update):
    
    # send goodbye greetings
    user = update.message.from_user
    logger.info("Sending email to : %s", user.first_name)
    
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
            
            CHOOSETABLE: [RegexHandler('^(Beach View|Poolside|Air-Conditioned Hall|Other)$', choice_of_table)],

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

    updater.idle()



if __name__ == '__main__':
    main()
