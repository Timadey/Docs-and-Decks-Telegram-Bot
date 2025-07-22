from fastapi import FastAPI
from pydantic import BaseModel

from config import Config
from repository.c2repository import C2Repository
from repository.repository import Repository
from attendance_bot import AttendanceBot
import threading

app = FastAPI()

attendance_checker = AttendanceBot(Config, Repository)
c2_repository = C2Repository()

@app.exception_handler(Exception)
async def global_exception_handler(request, ex):
    return {"message": "An unexpected error occurred", "success": False}

class RegisterDlbRequest(BaseModel):
    firstname: str
    lastname: str
    middlename: str|None
    gender: str
    email: str
    phone: str
    age_group: str
    msword_level: str
    msexcel_level: str
    mspptx_level: str
    education: str
    occupation: str
    motivation: str
    hear_source: str
    referral: str
    will_commit: bool
    created_at: str

class CheckExistRequest(BaseModel):
    column: str
    value: str
    sheet: str | None

@app.post("/register-dlb")
async def register_dlb(data: RegisterDlbRequest):
    success = c2_repository.register_participant(data.model_dump())
    return {"message": "Registration successful", "success": success}

@app.post("/check-exists")
async def check_exist(data: CheckExistRequest):
    exists = c2_repository.exists_in_google_sheet(data.column, data.value, data.sheet)
    return {"message": "Checked completed", "success": True, "data": {"exists": exists}}


def main():
    import uvicorn
    api_thread = threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000))
    api_thread.start()
    attendance_checker.initialize()


if __name__ == '__main__':
    main()






