from telegram.ext import Updater
import logging
from handlers import Handlers

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
        update.message.reply_text(f"Welcome to the {self.config.bot_name}! \n"
        "I mark your attendance during sessions. \n"
        "Please send your reference to get access to the group")
