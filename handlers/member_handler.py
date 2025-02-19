from telegram.ext import MessageHandler, Filters
from telegram import ParseMode
import logging

class MemberHandler:
    def __init__(self, bot, dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher
        self.logger = logging.getLogger(__name__)

    def setup(self):
        self.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.handle_new_member))
        self.dispatcher.add_handler(CommandHandler("validate_me", self.validate_me))

    def handle_new_member(self, update, context):
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                continue
            telegram_name = f"{member.first_name} {member.last_name or ''}".strip().lower()
            chat_id = update.effective_chat.id
            user_id = member.id
            mention = f"[{member.first_name}](tg://user?id={user_id})"
            if self.bot.repository.update_telegram_id(telegram_name, user_id):
                context.bot.send_message(chat_id=chat_id, text=f"✅ Welcome, {mention}! \n\n", parse_mode=ParseMode.MARKDOWN)
            else:
                warning_msg = context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"⚠️ Hi {mention}, we couldn't find you in our registered records.\n\n"
                        "📝 **Please update your Telegram name** to match the name you used in registration (**First Name & Last Name**).\n\n"
                        "🔧 To update your name, go to your [Profile Settings](tg://settings).\n\n"
                        "⏳ You have **5 minute** to update it, or you will be removed automatically!"
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                self.bot.pending_users[user_id] = {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "warning_msg_id": warning_msg.message_id,
                    "first_name": telegram_name,
                    "attempts": 0
                }
                context.job_queue.run_repeating(self.check_name_update, interval=50, first=50, context=user_id, name=str(user_id))

    def validate_me(self, update, context):
        telegram_id = update.effective_user.id
        telegram_name = f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip()
        chat_id = update.effective_chat.id
        mention = f"[{update.effective_user.first_name}](tg://user?id={telegram_id})"
        if self.bot.repository.find_member_by_telegram_id(telegram_id):
            update.message.reply_text("✅ You are a valid member and your Telegram is already linked!")
        elif self.bot.repository.update_telegram_id(telegram_name, telegram_id):
            update.message.reply_text("🔄 Your Telegram ID was linked successfully! You are now a valid member.")
        else:
            update.message.reply_text(
                text=(
                    "⚠️ We couldn't find you in our registered records.\n\n"
                    "📝 **Please update your Telegram name** to match the name you used in registration (**First Name & Last Name**) and try again.\n\n"
                    "🔧 To update your name, go to your [Profile Settings](tg://settings).\n\n"
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=update.message.message_id
            )

    def check_name_update(self, context):
        job = context.job
        user_id = int(job.name)
        if user_id not in self.bot.pending_users:
            job.schedule_removal()
            return
        user_data = self.bot.pending_users[user_id]
        chat_id = user_data["chat_id"]
        attempts = user_data["attempts"]
        try:
            member = context.bot.get_chat(user_id)
            telegram_name = f"{member.first_name} {member.last_name or ''}".strip().lower()
            mention = f"[{member.first_name}](tg://user?id={user_id})"
            if self.bot.repository.update_telegram_id(telegram_name, user_id):
                context.bot.send_message(chat_id=chat_id, text=f"✅ Thank you, {mention}! 🎉\n\nYour name is now correct", parse_mode=ParseMode.MARKDOWN)
                del self.bot.pending_users[user_id]
                job.schedule_removal()
            else:
                self.bot.pending_users[user_id]["attempts"] += 1
                if attempts >= 5:
                    context.bot.send_message(chat_id=chat_id, text=f"🚨 {mention} was removed for **not updating their name**.\n\n💡 Please update your name before rejoining the group.", parse_mode=ParseMode.MARKDOWN)
                    context.bot.kick_chat_member(chat_id, user_id)
                    self.bot.removed_users[user_id] = { "chat_id": chat_id, "user_id": user_id, "attempts": 0 }
                    context.job_queue.run_repeating(self.check_removed_users, interval=50, first=50, context=user_id, name=str(user_id))
                    del self.bot.pending_users[user_id]
                    job.schedule_removal()
        except Exception as e:
            self.logger.error(f"Error checking name update for {user_id}: {e}")
            job.schedule_removal()

    def check_removed_users(self, context):
        job = context.job
        user_id = int(job.name)
        if user_id not in self.bot.removed_users:
            job.schedule_removal()
            return
        user_data = self.bot.removed_users[user_id]
        chat_id = user_data["chat_id"]
        attempts = user_data["attempts"]
        try:
            member = context.bot.get_chat(user_id)
            telegram_name = f"{member.first_name} {member.last_name or ''}".strip().lower()
            if self.bot.repository.update_telegram_id(telegram_name, user_id):
                context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
                del self.bot.removed_users[user_id]
                job.schedule_removal()
            else:
                self.bot.removed_users[user_id]["attempts"] += 1
                if attempts >= 10:
                    del self.bot.pending_users[user_id]
                    job.schedule_removal()
        except Exception as e:
            self.logger.error(f"Error checking name update for removed user {user_id}: {e}")
            job.schedule_removal()