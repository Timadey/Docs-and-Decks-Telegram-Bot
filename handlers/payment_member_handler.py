from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from config import Config

class PaymentMemberHandler:
    def __init__(self, bot, dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher
        self.group_link = Config.GROUP_LINK
        self.removed_users = {}  # Track removed users for unban logic

    def setup(self):
        self.dispatcher.add_handler(CommandHandler("validate_me", self.validate_payment))
        self.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.handle_new_member))
        # Add handler for payment reference replies
        self.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), self.handle_payment_reference_reply))

    def handle_new_member(self, update, context):
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                continue
            chat_id = update.effective_chat.id
            user_id = member.id
            mention = f"[{member.first_name}](tg://user?id={user_id})"
            # Only allow if Telegram ID is linked
            if self.bot.repository.find_member_by_telegram_id(user_id):
                context.bot.send_message(chat_id=chat_id, text=f"✅ Welcome, {mention}! You are verified.", parse_mode=ParseMode.MARKDOWN)
            else:
                warning_msg = context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🚫 Hi {mention}, you are not in our registered records.\n\n"
                        "To join, please reply privately to validate your payment using /validate_me <your_payment_reference>.\n\n"
                        "If you believe this is a mistake, contact support."
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                context.bot.kick_chat_member(chat_id, user_id)
                self.removed_users[user_id] = {"chat_id": chat_id, "user_id": user_id, "attempts": 0}
                context.job_queue.run_repeating(self.check_removed_users, interval=60, first=60, context=user_id, name=str(user_id))

    def check_removed_users(self, context):
        job = context.job
        user_id = int(job.name)
        if user_id not in self.removed_users:
            job.schedule_removal()
            return
        user_data = self.removed_users[user_id]
        chat_id = user_data["chat_id"]
        try:
            # If user is now validated, unban them
            if self.bot.repository.find_member_by_telegram_id(user_id):
                context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
                del self.removed_users[user_id]
                job.schedule_removal()
        except Exception as e:
            job.schedule_removal()

    def validate_payment(self, update, context):
        chat_id = update.effective_chat.id
        telegram_id = update.effective_user.id
        args = context.args
        if not args:
            # Set flag to expect payment reference from this user
            context.user_data['awaiting_payment_reference'] = True
            update.message.reply_text(
                "💬 Please reply with your payment reference.",
                reply_to_message_id=update.message.message_id
            )
            return
        payment_reference = args[0].strip()
        self._process_payment_reference(update, context, payment_reference)

    def handle_payment_reference_reply(self, update, context):
        # Only process if we are expecting a payment reference from this user
        if context.user_data.get('awaiting_payment_reference'):
            payment_reference = update.message.text.strip()
            # Clear the flag
            context.user_data['awaiting_payment_reference'] = False
            self._process_payment_reference(update, context, payment_reference)

    def _process_payment_reference(self, update, context, payment_reference):
        chat_id = update.effective_chat.id
        telegram_id = update.effective_user.id
        try:
            email, row = self.bot.repository.find_participant_by_payment_reference(payment_reference)
            if not email:
                update.message.reply_text(
                    "❌ Payment reference not found. Please check and try again.",
                    reply_to_message_id=update.message.message_id
                )
                return
            # Update Telegram ID for this email
            success = self.bot.repository.update_telegram_id_by_email(email, telegram_id)
            if not success:
                update.message.reply_text(
                    "⚠️ Could not update your Telegram ID. Please contact support.",
                    reply_to_message_id=update.message.message_id
                )
                return
            update.message.reply_text(
                f"✅ Payment validated and Telegram linked!\n\nHere is your group link: {self.group_link}",
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=update.message.message_id
            )
        except Exception as e:
            update.message.reply_text(
                f"⚠️ Error validating payment: {str(e)}",
                reply_to_message_id=update.message.message_id
            ) 