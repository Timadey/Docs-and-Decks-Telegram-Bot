from config import Config
from repository import Repository
from attendance_bot import AttendanceBot

def main():
    attendance_checker = AttendanceBot(Config, Repository)
    attendance_checker.initialize()

if __name__ == '__main__':
    main()