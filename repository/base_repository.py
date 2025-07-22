from config import Config
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class BaseRepository:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(Config.gsheet_creds_file_path, scope)
    client = gspread.authorize(creds)

    def __init__(self):
        self.gsheet = self.client.open(Config.gsheet_name)

    def exists_in_google_sheet(self, column, value, sheet="Sheet1"):
        worksheet = self.gsheet.worksheet(sheet)
        all_rows = worksheet.get_all_values()
        if not all_rows:
            return False
        header = all_rows[0]
        try:
            col_index = header.index(column)
        except ValueError:
            return False
        if col_index is None:
            return False

        for row in all_rows[1:]:
            if len(row) > col_index and row[col_index] == value:
                return True
        return False

    def append_to_google_sheet(self, data, sheet="Sheet1"):
        worksheet = self.gsheet.worksheet(sheet)
        header = worksheet.get_all_values()[0]
        row = []
        for col in header:
            if col == 'created_at':
                from datetime import datetime
                row.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            else:
                row.append(data.get(col, ''))
        worksheet.append_row(row)
        return True