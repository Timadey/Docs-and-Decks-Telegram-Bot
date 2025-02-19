from telegram.ext import CommandHandler
from telegram import ParseMode

class RecordingHandler:
    def __init__(self, bot, dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher

    def setup(self):
        self.dispatcher.add_handler(CommandHandler("recordings", self.get_recordings))

    def get_recordings(self, update, context):
        try:
            recordings = self.bot.repository.get_recordings()
            if not recordings:
                context.bot.send_message(chat_id=update.effective_chat.id, text="📌 No session recordings available at the moment.")
                return
            message = "📚 *List of all session recording link*\n\n"
            for recording in recordings:
                message += f"📌 *{recording['Title']}*\n🔗 [Go to Video]({recording['Link']})\n\n"
            context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Error recordings: {str(e)}")