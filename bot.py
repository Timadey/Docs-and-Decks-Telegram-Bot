from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, JobQueue
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.utils.helpers import mention_markdown

from config import Config
from repository import Repository
import csv
import logging
import os
from io import BytesIO

# Load environment variables
PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load CSV data {full_name: email}
def load_participant_data(file_path):
    participants = {}
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                full_name = row["full_name"].strip().lower()  
                email = row["email"].strip()
                participants[full_name] = email
    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
    return participants

class AttendanceBot:
    def __init__(self, config, csv_path):
        self.TOKEN = config.bot_api
        self.repository = Repository()  
        self.pending_users = {}
        self.removed_users = {}  

    def initialize(self):
        updater = Updater(token=self.TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        job_queue = updater.job_queue  # JobQueue for scheduled tasks

        start_handler = CommandHandler('start', self.start, run_async=True)
        start_attendance_handler = CommandHandler('start_attendance',
                                                  self.start_attendance,
                                                  Filters.chat_type.groups,
                                                  run_async=True)
        attendance_handler = CallbackQueryHandler(
            self.mark_attendance, pattern='^' + r'present' + '$')
        end_attendance_handler = CallbackQueryHandler(
            self.end_attendance, pattern='^' + r'end_attendance' + '$')
        new_member_handler = MessageHandler(Filters.status_update.new_chat_members, self.handle_new_member)

        dispatcher.add_handler(CommandHandler("assignments", self.assignment_command))

        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(start_attendance_handler)
        dispatcher.add_handler(attendance_handler)
        dispatcher.add_handler(end_attendance_handler)
        dispatcher.add_handler(new_member_handler)

        # log all errors
        dispatcher.add_error_handler(self.error)

        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=self.TOKEN)
        updater.bot.setWebhook(f'{Config.server_url}/{self.TOKEN}')
        updater.idle()

    def start(self, update, context):
        update.message.reply_text("Welcome to the Docs and Decks Attendance Bot! \n"
        "I mark your attendance during sessions. \n"
        "In order to properly track your attendance, **please ensure your telegram first name and last name reflect the actual name** you used in registering for the program!")

    def assignment_command(self, update, context) -> None:
        """Handles the /assignment command by sending assignment submission details."""
        assignment_message = (
            "📌 *List of all assignment* 📌\n\n"
            "1️⃣ Preassessment Survey Submissions (30 marks): https://forms.gle/1ejGhpZ7EiYXfLSJ8. \n"
            
            "⚠️ *Late submissions results in half marks*"
        )
        update.message.reply_text(assignment_message, parse_mode="Markdown")


    def handle_new_member(self, update, context):
        """Handles when a new member joins"""
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:  # Skip if it's the bot itself
                continue

            telegram_name = f"{member.first_name} {member.last_name or ''}".strip().lower()  
            chat_id = update.effective_chat.id
            user_id = member.id

            mention = mention_markdown(user_id, f"{member.first_name} {member.last_name or ''}")

            if self.repository.update_telegram_id(telegram_name, user_id):
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Welcome, {mention}! \n\n",
                parse_mode=ParseMode.MARKDOWN,
                )

            else:
                warning_msg = context.bot.send_message(
                    chat_id=chat_id,
                    text= f"⚠️ Hi {mention}, we couldn't find you in our registered records.\n\n"
                            "📝 **Please update your Telegram name** to match the name you used in registration (**First Name & Last Name**).\n\n"
                            "🔧 To update your name, go to your [Profile Settings](tg://settings).\n\n"
                            "⏳ You have **5 minute** to update it, or you will be removed automatically!",
                    parse_mode=ParseMode.MARKDOWN,
                )

                self.pending_users[user_id] = {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "warning_msg_id": warning_msg.message_id,
                    "first_name": telegram_name,
                    "attempts": 0  
                }

                context.job_queue.run_repeating(self.check_name_update, interval=50, first=50, context=user_id, name=str(user_id))

    def check_name_update(self, context):
        """Checks if a user updated their name"""
        job = context.job
        user_id = int(job.name)  

        if user_id not in self.pending_users:
            job.schedule_removal()  # Stop checking if user is removed
            return

        user_data = self.pending_users[user_id]
        chat_id = user_data["chat_id"]
        attempts = user_data["attempts"]
        
        try:
            member = context.bot.get_chat(user_id)
            telegram_name = f"{member.first_name} {member.last_name or ''}".strip().lower()

            mention = mention_markdown(user_id, f"{member.first_name} {member.last_name or ''}")


            if self.repository.update_telegram_id(telegram_name, user_id):
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Thank you, {mention}! 🎉\n\n"
                        f"Your name is now correct",
                        parse_mode=ParseMode.MARKDOWN,
                )

                del self.pending_users[user_id]  
                job.schedule_removal()  
            else:
                self.pending_users[user_id]["attempts"] += 1
                if attempts >= 5:  # If the user has not updated after 5 checks
                    try:
                        context.bot.send_message(
                            chat_id=chat_id,
                            text=f"🚨 {mention} was removed for **not updating their name**.\n\n"
                                "💡 Please update your name before rejoining the group.",
                            parse_mode=ParseMode.MARKDOWN,
                        )

                        context.bot.kick_chat_member(chat_id, user_id)
                        self.removed_users[user_id] = {
                            "chat_id": chat_id,
                            "user_id": user_id,
                            "attempts": 0  
                        }
                        context.job_queue.run_repeating(self.check_removed_users, interval=50, first=50, context=user_id, name=str(user_id))

                       
                    except Exception as e:
                        logger.error(f"Failed to remove user {user_id}: {e}")
                    
                    del self.pending_users[user_id]  
                    job.schedule_removal()  
        except Exception as e:
            logger.error(f"Error checking name update for {user_id}: {e}")
            job.schedule_removal()
    
    def check_removed_users(self, context):
        """Checks if a user updated their name and unban them"""
        job = context.job
        user_id = int(job.name)  

        if user_id not in self.removed_users:
            job.schedule_removal()  # Stop checking if user is removed
            return

        user_data = self.removed_users[user_id]
        chat_id = user_data["chat_id"]
        attempts = user_data["attempts"]
        
        try:
            member = context.bot.get_chat(user_id)
            telegram_name = f"{member.first_name} {member.last_name or ''}".strip().lower()

            if self.repository.update_telegram_id(telegram_name, user_id):
                context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
                del self.removed_users[user_id]  
                job.schedule_removal()  
            else:
                self.removed_users[user_id]["attempts"] += 1
                if attempts >= 10:  # If the user has not updated after 10 checks
                    del self.pending_users[user_id]  
                    job.schedule_removal()  
        except Exception as e:
            logger.error(f"Error checking name update for removed user {user_id}: {e}")
            job.schedule_removal()
        
    def start_attendance(self, update, context):
        original_member = context.bot.get_chat_member(update.effective_chat.id,
                                                      update.effective_user.id)
        if original_member['status'] in ('creator', 'administrator'):
            if ('flag' in context.chat_data) and (context.chat_data['flag'] == 1):
                update.message.reply_text(
                    "Please close the current attendance first")
                return
            elif ('flag' not in context.chat_data) or (context.chat_data['flag'] == 0):
                self.repository.create_new_attendance_col()
                context.chat_data['flag'] = 1
                context.chat_data['attendees'] = 0
                context.chat_data['id'] = update.effective_chat.id
                keyboard = [
                    [InlineKeyboardButton("Present",
                                          callback_data='present')],
                    [InlineKeyboardButton("End Attendance (Admin only)",
                                          callback_data='end_attendance')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                self.message = update.message.reply_text(
                    "Please mark your attendance", reply_markup=reply_markup)
        else:
            # update.message.reply_text("Only admins can execute this command")
            pass
    
    def mark_attendance(self, update, context):
        query = update.callback_query
        if self.repository.mark_attendance(update.effective_user.id):
            context.chat_data['attendees'] += 1

            context.bot.answer_callback_query(
                callback_query_id=query.id,
                text=f"You are the #{context.chat_data['attendees']} to mark attendance. Score : 10 marks",
                show_alert=True)
        else:
            context.bot.answer_callback_query(
                callback_query_id=query.id,
                text="Your attendance is already marked",
                show_alert=True)
        query.answer()

    def end_attendance(self, update, context):
        query = update.callback_query
        original_member = context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id)
        
        if original_member['status'] in ('creator', 'administrator'):
            if (context.chat_data['id'] != update.effective_chat.id):
                return
            
            attendance_count = context.chat_data['attendees']
            
            query.answer()
            context.bot.edit_message_text(
                text="Attendance is over. \n" +
                str(attendance_count) +
                " participants marked attendance.\n",
                # + "Here is the list:\n" + str1,
                chat_id=self.message.chat_id,
                message_id=self.message.message_id,
                parse_mode=ParseMode.MARKDOWN)
            
            context.chat_data['flag'] = 0
            context.chat_data['attendees'] = 0
        else:
            context.bot.answer_callback_query(
                callback_query_id=query.id,
                text="This command can be executed by admin only",
                show_alert=True)
            query.answer()

    def error(self, update, context):
        logger.warning('Update "%s" caused error "%s"', update,
                       context.error)

def main():
    csv_path = Config.participant_csv_path
    attendance_checker = AttendanceBot(Config, csv_path)
    attendance_checker.initialize()

if __name__ == '__main__':
    main()
