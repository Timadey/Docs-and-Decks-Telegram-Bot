from config import Config
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class Repository:

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(Config.gsheet_creds_file_path, scope)
    client = gspread.authorize(creds)

    gsheet = client.open(Config.gsheet_name)
    participants_sheet = gsheet.worksheet("participants")


    def update_telegram_id(self, telegram_name, telegram_id):
        """Finds a user by name and updates their Telegram ID"""
        if self.telegram_id_exists(telegram_id):
            return True
        
        full_names = self.participants_sheet.col_values(2)
        full_name_parts = set(telegram_name.strip().lower().split())

        for i, name in enumerate(full_names, start=1): 
            if set(name.strip().lower().split()[:2]) == full_name_parts:
                self.participants_sheet.update_cell(i, 4, telegram_id)  
                return True
        
        return False
    
    def telegram_id_exists(self, telegram_id):
        telegram_ids = self.participants_sheet.col_values(4)
        if telegram_id in telegram_ids:
            return True
        return False
    
    def create_new_attendance_col(self):
        """Creates a new column in Google Sheets for attendance"""
        date_str = datetime.today().strftime('%b %d')

        # Get the total number of columns in the sheet
        header = self.participants_sheet.row_values(1)  # Get header row
        num_cols = len(header)  
        new_col_index = num_cols + 1  

        # Expand sheet if needed
        if new_col_index > self.participants_sheet.col_count:
            self.participants_sheet.add_cols(new_col_index - self.participants_sheet.col_count)

        # Add the new attendance column
        self.participants_sheet.update_cell(1, new_col_index, f"Attendance - {date_str}")

        return new_col_index 


    def mark_attendance(self, telegram_id, marks=10):
        """Finds a user by Telegram ID and assigns attendance marks in the latest column if not already marked."""
        
        try:
            cell = self.participants_sheet.find(str(telegram_id), in_column=4)  # Locate Telegram ID in column 4
            headers = self.participants_sheet.row_values(1)  # Get column headers
            last_col_index = len(headers)  # Identify the last attendance column
            
            # Check if attendance is already marked
            existing_mark = self.participants_sheet.cell(cell.row, last_col_index).value
            if existing_mark:  # If there's already a value, don't overwrite
                return False  # Attendance already marked
            
            # Mark attendance
            self.participants_sheet.update_cell(cell.row, last_col_index, marks)
            return True  # Successfully marked
        except Exception:
            return False  # Telegram ID not found
    
    def count_last_attendance(self):
        """
        Finds the last attendance column and counts the number of non-empty rows.
        
        :return: Total rows with values in the last attendance column
        """
        headers = self.participants_sheet.row_values(1)  # Get column headers
        last_attendance_col = len(headers)  # Identify the last attendance column
        
        col_values = self.participants_sheet.col_values(last_attendance_col)  # Get values in that column
        non_empty_rows = len([val for val in col_values if val.strip()])  # Count non-empty rows
        
        return non_empty_rows - 1
 