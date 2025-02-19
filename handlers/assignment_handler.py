from telegram.ext import CommandHandler
from telegram import ParseMode

class AssignmentHandler:
    def __init__(self, bot, dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher

    def setup(self):
        self.dispatcher.add_handler(CommandHandler("assignments", self.get_assignment))

    def get_assignment(self, update, context):
        try:
            assignments = self.bot.repository.get_assignments()
            telegram_id = update.effective_user.id
            can_view_score = False
            try:
                member = self.repository.get_member_by_telegram_id(telegram_id)
                member_email = None

                if member:
                    member_email = member.get('Email')
                    if member_email:  # If email is present, they can view scores
                        can_view_score = True
            except ValueError as e:
                can_view_score = False

            if not assignments:
                update.message.reply_text("📌 No assignments available at the moment.")
                return

            message = "📚 *List of all assignments*\n\n"
           

            for assignment in assignments:
                assignment_sheet = assignment['Sheet'].strip()
                score_text = "❌ *Score:* Not available"

                if can_view_score:
                    score = self.bot.repository.get_score(assignment_sheet, member_email)
                    score_text = f"{"✅" if score else "❌"} *Score:* {score}/{assignment['Score']}"

                message += (
                    f"📌 *{assignment['Date']}: {assignment['Title']}*\n"
                    f"_Due on {assignment['Deadline']} | [View Assignment]({assignment['Submission link']})_\n"
                    f"{score_text}\n\n"
                )

            if not can_view_score:
                message += (
                    "⚠️ _Your Telegram is not linked, so you can't see your scores._\n"
                    "👉 _Run `/validate_me` to link your Telegram and access your scores._"
                )

            message += "\n⚠️ *Late submissions result in half marks.*"

            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        except Exception as e:
            update.message.reply_text(f"⚠️ Error retrieving assignments: {str(e)}")
