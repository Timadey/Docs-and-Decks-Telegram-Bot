from telegram.ext import CommandHandler
from telegram import ParseMode
from utils import escape_markdown

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
                member = self.bot.repository.get_member_by_telegram_id(telegram_id)
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
                assignment_title = escape_markdown(assignment['Title'])
                assignment_deadline = escape_markdown(assignment['Deadline'])
                assignment_link = assignment['Submission link']
                assignment_score = escape_markdown(str(assignment['Score']))
                assignment_date = escape_markdown(assignment['Date'])

                assignment_sheet = assignment['Sheet'].strip()
                score_text = "❌ *Score:* Not available"

                if can_view_score:
                    score = self.bot.repository.get_score(assignment_sheet, member_email)
                    icon = "✅" if score else "❌"
                    score_text = f"{icon} *Score:* {escape_markdown(str(score))}/{assignment_score}"

                message += (
                    f"📌 *{assignment_date}: {assignment_title}*\n"
                    f"_Due on {assignment_deadline}_ | [View Assignment]({assignment_link})\n"
                    f"{score_text}\n\n"
                )

            if not can_view_score:
                message += (
                    "⚠️ *Your Telegram is not linked, so you can't see your scores.*\n"
                    "👉 Run `/validate_me` to link your Telegram and access your scores."
                )

            message += "\n⚠️ *Late submissions result in half marks.*"

            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        except Exception as e:
            update.message.reply_text(f"⚠️ Error retrieving assignments: {str(e)}")
