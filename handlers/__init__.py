from handlers.attendance_handler import AttendanceHandler
from handlers.resource_handler import ResourceHandler
from handlers.assignment_handler import AssignmentHandler
from handlers.recording_handler import RecordingHandler
from handlers.member_handler import MemberHandler
from handlers.score_handler import OverallScoreHandler

class Handlers:
    def __init__(self, bot, dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher

    def setup_handlers(self):
        AttendanceHandler(self.bot, self.dispatcher).setup()
        ResourceHandler(self.bot, self.dispatcher).setup()
        AssignmentHandler(self.bot, self.dispatcher).setup()
        RecordingHandler(self.bot, self.dispatcher).setup()
        MemberHandler(self.bot, self.dispatcher).setup()
        OverallScoreHandler(self.bot, self.dispatcher).setup()
    