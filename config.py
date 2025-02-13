#!/usr/bin/python3

import os

class Config:
    bot_api = os.environ.get("bot_api", None) 
    participant_csv_path = os.environ.get("participant_csv_path", None)
    gsheet_creds_file_path = os.environ.get("gsheet_creds_file_path", None) 
    gsheet_name = os.environ.get("gsheet_name", None)
    server_url = os.environ.get("server_url", None)

