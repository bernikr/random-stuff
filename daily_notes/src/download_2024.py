import datetime
import os
from pathlib import Path

import gspread
from dotenv import load_dotenv

from daily_notes import NotesApi

HAPPINESS_SELECTION = ["", "Viel schlechter als Normal", "Schlechter als Normal", "Normal", "Besser als Normal",
                       "Viel besser als Normal"]

def iint(x):
    try:
        return int(x)
    except ValueError:
        return None

def row_to_note_data(r):
    d = {}

    d['happiness'] = HAPPINESS_SELECTION.index(r['Persönliches Befinden'])
    d['sick'] = bool(r['Krank?'])

    try:
        h, m, _ = r['Schlaf'].split(":")
        d['sleep-duration'] = round(int(h) + int(m) / 60, 2)
    except:
        pass

    d['shits'] = iint(r['Toilettengänge'])
    d['sex'] = iint(r['Sex'])
    d['faps'] = iint(r['Masturbiert'])

    if r['Freunde getroffen']:
        d['friends-met'] = r['Freunde getroffen'].split(", ")
    else:
        d['friends-met'] = None
    if r['Sport']:
        d['sport'] = r['Sport'].split(", ")
    else:
        d['sport'] = None
    if r['Tätigkeiten']:
        d['activities'] = r['Tätigkeiten'].split(", ")
    else:
        d['activities'] = None

    d['game-played'] = r['Welches Spiel gespielt']
    d['book-read'] = r['Buch fertig gelesen']

    try:
        h, m, _ = r['Medienwatchtime'].split(":")
        d['watchtime'] = round(int(h) + int(m) / 60,2)
    except:
        d['watchtime'] = 0

    if r['Diät']:
        d['food'] = r['Diät'].split(", ")
    d['weed'] = iint(r['Weed'])

    d['drinks'] = []
    for k, v in r.items():
        if k.startswith("Getrunken ") and v:
            d['drinks'].append(f"{v} {k[11:-1]}")

    return d


if __name__ == '__main__':
    load_dotenv()
    OBSIDIAN_FOLDER = os.getenv('OBSIDIAN_FOLDER')
    STATS_NAME = os.getenv('STATS_NAME')
    STATS_SHEET = os.getenv('STATS_SHEET')

    n = NotesApi(OBSIDIAN_FOLDER)

    start = datetime.date(2024, 1, 1)
    end = datetime.date(2024, 9, 15)
    days = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days + 1)]

    gc = gspread.service_account(filename=Path(__file__).parent.parent / "service_account.json")
    stats_file = gc.open_by_key(STATS_SHEET)
    data_sheet = stats_file.worksheet("Raw-Data")
    data = data_sheet.get_all_records()
    for r in data:
        if r["Name"] == STATS_NAME:
            date = datetime.datetime.strptime(r["Datum"], "%d.%m.%Y").date()
            if date in days:
                note_data = row_to_note_data(r)
                n.add_data(date, note_data, overwrite=True)
