from config import Config
from repository.base_repository import BaseRepository


class C2Repository(BaseRepository):

    def __init__(self):
        super().__init__()
        self.gsheet = self.client.open(Config.cohort2sheet)

    def register_participant(self, participant_data):
        return self.append_to_google_sheet(participant_data, sheet="registration")