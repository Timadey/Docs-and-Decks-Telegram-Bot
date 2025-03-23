from telegram.ext import CommandHandler
from telegram import ParseMode
from utils import escape_markdown

class OverallScoreHandler:
    def __init__(self, bot, dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher

    def setup(self):
        self.dispatcher.add_handler(CommandHandler("my_score", self.get_overall_score))

    def get_overall_score(self, update, context):
        try:
            telegram_id = update.effective_user.id
            member = None
            member_email = None

            try:
                member = self.bot.repository.get_member_by_telegram_id(telegram_id)

                if member:
                    member_email = member.get('Email address')
            except ValueError:
                update.message.reply_text(
                    "⚠️ Your Telegram is not linked, so we can't retrieve your score.\n"
                    "👉 Run /validate_me to link your Telegram.",
                    reply_to_message_id=update.message.message_id
                )
                return

            if not member_email:
                update.message.reply_text("⚠️ No email found for your profile, so we can't fetch your score.")
                return

            # Fetch overall score
            overall_score_data = self.bot.repository.get_overall_score(member_email)

            if not overall_score_data:
                update.message.reply_text("⚠️ No score data found for you.")
                return

            # Determine eligibility emoji and message
            if overall_score_data.get('status', 'N/A') == "Eligible":
                eligibility_emoji = "✅"
                final_message = "🎉 Congratulations! You are currently up to the certification requirements. Keep up the great work! 🚀"
            else:
                eligibility_emoji = "❌"
                final_message = "💡 You need at least 50% to be eligible! Don't give up! Attend sessions, do your assignments well, and you'll improve. You can do this! 💪"

            # Format the response message
            message = (
                f"📊 <b>Your Overall Score</b>\n\n"
                f"👤 <b>Name:</b> {overall_score_data.get('Full Name', 'N/A')}\n"
                f"📋 <b>Overall Attendance:</b> {overall_score_data.get('Attendance', 'N/A')}\n"
                f"📝 <b>Pre-Assessment:</b> {overall_score_data.get('pre-assessment', 'N/A')}\n"
                f"📄 <b>MS Word 1 Home Away:</b> {overall_score_data.get('msword1', 'N/A')}\n"
                f"📄 <b>MS Word 2 Insert If You Can:</b> {overall_score_data.get('msword2', 'N/A')}\n"
                f"📄 <b>MS Word 4 Love Feast:</b> {overall_score_data.get('msword4', 'N/A')}\n"
                f"🔢 <b>Total Score:</b> {overall_score_data.get('sum', 'N/A')} / {overall_score_data.get('total_score', 'N/A')}\n"
                f"{eligibility_emoji} <b>Certification Status:</b> {overall_score_data.get('status', 'N/A')}\n\n"
                f"{final_message}"
            )

            update.message.reply_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.message.message_id
            )

        except Exception as e:
            update.message.reply_text(f"⚠️ Error retrieving your overall score: {str(e)}")
