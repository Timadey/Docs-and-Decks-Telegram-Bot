from telegram.ext import CommandHandler
from telegram import ParseMode

class ResourceHandler:
    def __init__(self, bot, dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher

    def setup(self):
        self.dispatcher.add_handler(CommandHandler("resources", self.get_resources))

    def get_resources(self, update, context):
        try:
            resources = self.bot.repository.get_resources()
            if not resources:
                context.bot.send_message(chat_id=update.effective_chat.id, text="📌 No resources available at the moment.")
                return
            message = "📚 *List of all resources*\n\n"
            for res in resources:
                message += f"📌 *{res['Title']}*\n🔗 [{res['Location']} link]({res['Link']})\n\n"
            context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Error fetching resources: {str(e)}")