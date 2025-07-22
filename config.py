#!/usr/bin/python3

import os
from dotenv import load_dotenv
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
load_dotenv()

class Config:
    port = int(os.environ.get('PORT', 5000))
    bot_api = os.environ.get("bot_api", None) 
    participant_csv_path = os.environ.get("participant_csv_path", None)
    gsheet_creds_file_path = os.environ.get("gsheet_creds_file_path", None) 
    gsheet_name = os.environ.get("gsheet_name", None)
    server_url = os.environ.get("server_url", None)
    cohort2sheet=os.environ.get("cohort2sheet", None)
    GROUP_LINK = os.environ.get("GROUP_LINK", "https://t.me/your_group_link_here")

