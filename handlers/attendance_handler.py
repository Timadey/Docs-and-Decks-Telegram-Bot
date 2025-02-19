from telegram.ext import CommandHandler, CallbackQueryHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

class AttendanceHandler:
    def __init__(self, bot, dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher

    def setup(self):
        self.dispatcher.add_handler(CommandHandler('start', self.start, run_async=True))
        self.dispatcher.add_handler(CommandHandler("start_attendance", self.start_attendance, Filters.chat_type.groups, run_async=True))
        self.dispatcher.add_handler(CallbackQueryHandler(self.mark_attendance, pattern='^present$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.end_attendance, pattern='^end_attendance$'))

    def start(self, update, context):
        update.message.reply_text("Welcome to the Docs and Decks Attendance Bot! \n"
        "I mark your attendance during sessions. \n"
        "In order to properly track your attendance, **please ensure your telegram first name and last name reflect the actual name** you used in registering for the program!")

    def start_attendance(self, update, context):
        original_member = context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        if original_member['status'] in ('creator', 'administrator'):
            if 'flag' in context.chat_data and context.chat_data['flag'] == 1:
                update.message.reply_text("Please close the current attendance first")
                return
            elif 'flag' not in context.chat_data or context.chat_data['flag'] == 0:
                self.bot.repository.create_new_attendance_col()
                context.chat_data['flag'] = 1
                context.chat_data['attendees'] = 0
                context.chat_data['id'] = update.effective_chat.id
                keyboard = [
                    [InlineKeyboardButton("Present", callback_data='present')],
                    [InlineKeyboardButton("End Attendance (Admin only)", callback_data='end_attendance')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                self.message = update.message.reply_text("Please mark your attendance", reply_markup=reply_markup)
        else:
            pass

    def mark_attendance(self, update, context):
        query = update.callback_query
        try:
            if self.bot.repository.mark_attendance(update.effective_user.id):
                context.chat_data['attendees'] += 1
                context.bot.answer_callback_query(callback_query_id=query.id, text=f"You are the #{context.chat_data['attendees']} to mark attendance.\n Score : 10 marks", show_alert=True)
            else:
                context.bot.answer_callback_query(callback_query_id=query.id, text="Your attendance is already marked", show_alert=True)
        except Exception as e:
            context.bot.answer_callback_query(callback_query_id=query.id, text="Error marking attendance. Seems like your telegram is yet to be linked. Please use /validate_me command to link your telegram and try again", show_alert=True)
        query.answer()

    def end_attendance(self, update, context):
        query = update.callback_query
        original_member = context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        if original_member['status'] in ('creator', 'administrator'):
            if context.chat_data['id'] != update.effective_chat.id:
                return
            attendance_count = context.chat_data['attendees']
            query.answer()
            context.bot.edit_message_text(
                text=f"Attendance is over. \n{attendance_count} participants marked attendance.\n",
                chat_id=self.message.chat_id,
                message_id=self.message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
            context.chat_data['flag'] = 0
            context.chat_data['attendees'] = 0
        else:
            context.bot.answer_callback_query(callback_query_id=query.id, text="This command can be executed by admin only", show_alert=True)
            query.answer()