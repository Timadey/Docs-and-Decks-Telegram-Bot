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
    assignments_sheet = gsheet.worksheet("assignments")
    recordings_sheet = gsheet.worksheet("recordings")
    resources_sheet = gsheet.worksheet("resources")
    score_sheet = gsheet.worksheet("score_sheet")

    @classmethod
    def get_assignments(cls):
        return cls.assignments_sheet.get_all_records()

    @classmethod
    def get_resources(cls):
        return cls.resources_sheet.get_all_records()

    @classmethod
    def get_recordings(cls):
        return cls.recordings_sheet.get_all_records()

    @classmethod
    def get_overall_score(self, member_email):
        """Fetches all scores for a user based on their email."""
        try:
            if not member_email:
                return None  # Email is required

            headers = self.score_sheet.row_values(1)  # Fetch column headers

            # Locate the 'Email address' column index
            email_index = headers.index("Email address") + 1  # Google Sheets uses 1-based index

            # Locate the row containing the member's email
            cell = self.score_sheet.find(str(member_email), in_column=email_index)
            if not cell:
                return None  # Email not found

            # Fetch all scores from that row
            scores = self.score_sheet.row_values(cell.row)

            # Create a dictionary mapping headers to values
            scores_dict = {headers[i]: scores[i] if i < len(scores) else "N/A" for i in range(len(headers))}
            total_score = self.assignments_sheet.acell("M2").value

            return {
                "Full Name": scores_dict.get("Full Name", "N/A"),
                "Attendance": scores_dict.get("Attendance", "N/A"),
                "pre-assessment": scores_dict.get("pre-assessment", "N/A"),
                "msword1": scores_dict.get("msword1", "N/A"),
                "msword2": scores_dict.get("msword2", "N/A"),
                "msword4": scores_dict.get("msword4", "N/A"),
                "sum": scores_dict.get("sum", "N/A"),  # Student's Total score
                "status": scores_dict.get("status", "N/A"),  # Certification status
                "total_score" :  total_score
            }

        except ValueError:
            return None  # If the email is not found
        except Exception as e:
            raise RuntimeError(f"Error retrieving scores: {e}")

    
    @classmethod
    def get_score(cls, assignment_sheet, member_email):
        """Finds a user's score in the assignment sheet based on their email."""
        try:
            if not assignment_sheet:
                return 0
            sheet = cls.gsheet.worksheet(assignment_sheet)
            headers = sheet.row_values(1)
            
            # Find the column indexes for 'Email' and 'Score'
            email_index = headers.index("Email address") + 1  # Convert to 1-based index
            score_index = headers.index("Score") + 1  # Convert to 1-based index
            
            # Find the row where the Email is located
            cell = sheet.find(str(member_email), in_column=email_index)
            if not cell:
                return 0  
            # Fetch the score from the corresponding row
            score = sheet.cell(cell.row, score_index).value
            
            return score if score else 0  
        except ValueError:
            return 0  # If the email is not found in the sheet
        except Exception as e:
            raise RuntimeError(f"Error retrieving score: {e}")


    @classmethod
    def __find_member_row_by_telegram_id(cls, telegram_id):
        """Finds a user by Telegram ID and returns their row as a dictionary."""
        try:
            headers = cls.participants_sheet.row_values(1) 
            telegram_col_index = headers.index("Telegram ID") + 1  # Convert to 1-based index
            cell = cls.participants_sheet.find(str(telegram_id), in_column=telegram_col_index)
            if not cell:
                raise ValueError(f"Telegram ID {telegram_id} not found.")
            return cell.row
        except ValueError as ve:
            raise ve  # Handle specific "not found" cases separately if needed
        except Exception as e:
            raise RuntimeError(f"Error retrieving user data: {e}")

    @classmethod
    def get_member_by_telegram_id(cls, telegram_id):
        """Finds a user by Telegram ID and returns their row as a dictionary."""
        try:
            headers = cls.participants_sheet.row_values(1) 
            cell_row = cls.__find_member_row_by_telegram_id(telegram_id)
            user_row = cls.participants_sheet.row_values(cell_row)
            # Convert row values into a dictionary using column names
            return dict(zip(headers, user_row))
        except ValueError as ve:
            raise ve  # Handle specific "not found" cases separately if needed
        except Exception as e:
            raise RuntimeError(f"Error retrieving user data: {e}")


    @classmethod
    def find_member_by_telegram_id(cls, telegram_id):
        """Checks if the Telegram ID exists in the Google Sheet"""
        telegram_ids = cls.participants_sheet.col_values(4)[1:]  
        return str(telegram_id) in telegram_ids

    @classmethod
    def find_participant_by_name(cls, telegram_name):
        """Finds a user by name and updates their Telegram ID"""
        full_names = cls.participants_sheet.col_values(2)
        # full_name_parts = set(telegram_name.strip().lower().split())
        name_parts =  telegram_name.strip().lower().split()

        tg_first_name = name_parts[0]
        tg_last_name = "".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        full_name_parts = tg_first_name.strip().split() + tg_last_name.strip().split()
        full_name_parts = set(full_name_parts)

        for i, name in enumerate(full_names, start=1):
            names = name.strip().lower().split()
            last_first = set(names[:2])
            last_middle = set()
            everything = set()
            if len(names) > 2:
                last_middle = set([names[0], names[2]])
                everything = set(names)
            if last_first == full_name_parts or last_middle == full_name_parts or everything == full_name_parts:
                return i
        return False
    
    @classmethod
    def update_telegram_id(cls, telegram_name, telegram_id):
        """Finds a user by name and updates their Telegram ID"""
        if cls.telegram_id_exists(telegram_id):
            return True
        name_row = cls.find_participant_by_name(telegram_name)
        if name_row:
                cls.participants_sheet.update_cell(name_row, 4, telegram_id)  
                return True
        return False
    
    @classmethod
    def telegram_id_exists(cls, telegram_id):
        telegram_ids = cls.participants_sheet.col_values(4)
        if telegram_id in telegram_ids:
            return True
        return False
    
    @classmethod
    def create_new_attendance_col(cls):
        """Creates a new column in Google Sheets for attendance"""
        date_str = datetime.today().strftime('%b %d')

        # Get the total number of columns in the sheet
        header = cls.participants_sheet.row_values(1)  # Get header row
        num_cols = len(header)  
        new_col_index = num_cols + 1  

        # Expand sheet if needed
        if new_col_index > cls.participants_sheet.col_count:
            cls.participants_sheet.add_cols(new_col_index - cls.participants_sheet.col_count)

        # Add the new attendance column
        cls.participants_sheet.update_cell(1, new_col_index, f"Attendance - {date_str}")

        return new_col_index 


    @classmethod
    def mark_attendance(cls, telegram_id, marks=10):
        """Finds a user by Telegram ID and assigns attendance marks in the latest column if not already marked."""
        
        try:
            cell = cls.participants_sheet.find(str(telegram_id), in_column=4)  # Locate Telegram ID in column 4
            headers = cls.participants_sheet.row_values(1)  # Get column headers
            last_col_index = len(headers)  # Identify the last attendance column
            
            # Check if attendance is already marked
            existing_mark = cls.participants_sheet.cell(cell.row, last_col_index).value
            if existing_mark:  # If there's already a value, don't overwrite
                return False  # Attendance already marked
            
            # Mark attendance
            cls.participants_sheet.update_cell(cell.row, last_col_index, marks)
            return True  # Successfully marked
        except Exception as e:
            raise Exception(f"Error marking attendance for Telegram ID {telegram_id}: {str(e)}")
    
    @classmethod
    def count_last_attendance(cls):
        """
        Finds the last attendance column and counts the number of non-empty rows.
        
        :return: Total rows with values in the last attendance column
        """
        headers = cls.participants_sheet.row_values(1)  # Get column headers
        last_attendance_col = len(headers)  # Identify the last attendance column
        
        col_values = cls.participants_sheet.col_values(last_attendance_col)  # Get values in that column
        non_empty_rows = len([val for val in col_values if val.strip()])  # Count non-empty rows
        
        return non_empty_rows - 1
 
