from telegram.ext import Updater
import logging
from handlers import Handlers
from repository import Repository

class AttendanceBot:
    def __init__(self, config, repo):
        self.TOKEN = config.bot_api
        self.config = config
        self.repository = repo  
        self.pending_users = {}
        self.removed_users = {}

    def initialize(self):
        updater = Updater(token=self.TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        handlers = Handlers(self, dispatcher)
        handlers.setup_handlers()

        # log all errors
        dispatcher.add_error_handler(self.error)

        updater.start_webhook(listen="0.0.0.0", port=self.config.port, url_path=self.TOKEN)
        updater.bot.setWebhook(f'{self.config.server_url}/{self.TOKEN}')
        updater.idle()

    def error(self, update, context):
        logger = logging.getLogger(__name__)
        logger.warning('Update "%s" caused error "%s"', update, context.error)
    
    def start(self, update, context):
        update.message.reply_text("Welcome to the Docs and Decks Attendance Bot! \n"
        "I mark your attendance during sessions. \n"
        "In order to properly track your attendance, **please ensure your telegram first name and last name reflect the actual name** you used in registering for the program!")
