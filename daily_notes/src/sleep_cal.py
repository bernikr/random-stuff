import os
import re
from datetime import datetime, timedelta
from itertools import groupby

from dotenv import load_dotenv
from icalevents import icalevents

from daily_notes import NotesApi, CreateMode

DURATION_REGEX = re.compile(r"Duration:<b>(\d+):(\d+)</b>")


def get_sleep_minutes(event: icalevents.Event) -> int:
    h, m = DURATION_REGEX.findall(event.description)[0]
    return int(h) * 60 + int(m)


if __name__ == '__main__':
    load_dotenv()
    SLEEP_ICAL = os.getenv('SLEEP_ICAL')
    OBSIDIAN_FOLDER = os.getenv('OBSIDIAN_FOLDER')

    n = NotesApi(OBSIDIAN_FOLDER)

    all_events = icalevents.events(SLEEP_ICAL, start=datetime.now() - timedelta(days=3))
    for day, events in groupby(sorted(all_events, key=lambda e: e.end.date()), lambda e: e.end.date()):
        total_sleep = sum(map(get_sleep_minutes, events))
        n.add_data(day, {"sleep-duration": round(total_sleep / 60, 2)},
                   overwrite=True, create=CreateMode.TEMPLATE)
