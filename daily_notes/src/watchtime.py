import datetime
import os
import requests
from dotenv import load_dotenv

from daily_notes import NotesApi

load_dotenv()
HA_TOKEN = os.getenv('HA_TOKEN')
HA_URL = os.getenv('HA_URL')
OBSIDIAN_FOLDER = os.getenv('OBSIDIAN_FOLDER')


def write_watchtime(notes: NotesApi, date: datetime.date, entity: str):
    res = requests.get(f'{HA_URL}/api/states/{entity}', headers={'Authorization': f'Bearer {HA_TOKEN}'}).json()
    try:
        time = float(res['state'])
    except ValueError:
        time = 0
    notes.add_data(date, {"watchtime": round(time, 2)}, overwrite=True)


if __name__ == '__main__':
    n = NotesApi(OBSIDIAN_FOLDER)
    write_watchtime(n, datetime.date.today(), "sensor.media_watchtime_today")
    write_watchtime(n, datetime.date.today() - datetime.timedelta(days=1), "sensor.media_watchtime_yesterday")
