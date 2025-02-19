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
            member = None
            member_email = None

            try:
                member = self.bot.repository.get_member_by_telegram_id(telegram_id)

                if member:
                    member_email = member.get('Email address')
                    if member_email:  # If email is present, they can view scores
                        can_view_score = True
            except ValueError:
                update.message.reply_text(
                    "⚠️ Your Telegram is not linked, so your scores may not be visible.\n"
                    "👉 Run /validate_me to link your Telegram.",
                    reply_to_message_id=update.message.message_id
                )

            if not assignments:
                update.message.reply_text("📌 No assignments available at the moment.")
                return

            message = "<b>📚 List of all assignments</b>\n\n"

            for assignment in assignments:
                assignment_sheet = assignment['Sheet'].strip()
                score = self.bot.repository.get_score(assignment_sheet, member_email) if member else None
                assignment_score = assignment['Score']

                # Score display logic
                score_text = (
                    f"&#9989; <b>Score:</b> <code>{score}/{assignment_score}</code>"
                    if score is not None else
                    "&#10060; <b>Score:</b> Not available"
                )

                # Assignment details
                message += (
                    f"📌 <b>{assignment['Date']}: {assignment['Title']}</b>\n"
                    f"<i>Due on {assignment['Deadline']} | "
                    f"<a href='{assignment['Submission link']}'>View Assignment</a></i>\n"
                    f"{score_text}\n\n"
                )
            message += "\n⚠️ <i>Late submissions result in half marks.</i>"

            update.message.reply_text(
                message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_to_message_id=update.message.message_id
            )

        except Exception as e:
            update.message.reply_text(f"⚠️ Error retrieving assignments: {str(e)}")
