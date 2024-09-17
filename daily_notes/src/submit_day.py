import datetime
import os
from itertools import groupby
from pathlib import Path

from dotenv import load_dotenv
import gspread
from gspread.utils import ValueInputOption, InsertDataOption

from daily_notes import NotesApi

HAPPINESS_SELECTION = ["", "Viel schlechter als Normal", "Schlechter als Normal", "Normal", "Besser als Normal",
                       "Viel besser als Normal"]


def note_data_to_row(data: dict, date: datetime.date, name: str) -> dict:
    row = {
        "Zeitstempel": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "Datum": date.strftime("%d.%m.%Y"),
        "Name": name
    }

    if (d := data.get("happiness")) is not None:
        row["Persönliches Befinden"] = HAPPINESS_SELECTION[d]

    if data.get("sick", False):
        row["Krank?"] = "Ja"

    if (d := data.get("sleep-duration")) is not None:
        h, m = divmod(int(d * 60), 60)
        row["Schlaf"] = f"{h:d}:{m:02d}:00"

    if (d := data.get("shits")) is not None:
        row["Toilettengänge"] = d

    if (d := data.get("sex")) is not None:
        row["Sex"] = d

    if (d := data.get("faps")) is not None:
        row["Masturbiert"] = d

    if (d := data.get("friends-met")) is not None:
        row["Freunde getroffen"] = ", ".join(d)

    if (d := data.get("sport")) is not None:
        row["Sport"] = ", ".join(d)

    if (d := data.get("activities")) is not None:
        row["Tätigkeiten"] = ", ".join(d)

    if (d := data.get("game-played")) is not None:
        row["Welches Spiel gespielt"] = d

    if (d := data.get("book-read")) is not None:
        row["Buch fertig gelesen"] = d

    if (d := data.get("watchtime")) is not None:
        h, m = divmod(int(d * 60), 60)
        row["Medienwatchtime"] = f"{h:d}:{m:02d}:00"

    if (d := data.get("food")) is not None:
        row["Diät"] = ", ".join(d)

    if (d := data.get("drinks")) is not None:
        drinks = sorted([x.split(" ", 1) for x in d], key=lambda x: x[1])
        drinks = [(drink, max(int(x[0]) for x in amounts)) for drink, amounts in groupby(drinks, lambda x: x[1])]
        for drink, amount in drinks:
            row[f"Getrunken [{drink}]"] = amount

    if (d := data.get("weed")) is not None:
        row["Weed"] = d

    return row


def submit_day(api: NotesApi, name: str, date: datetime.date):
    data = api.get_data(date)
    row_data = note_data_to_row(data, date, name)

    gc = gspread.service_account(filename=Path(__file__).parent.parent / "service_account.json")
    wks = gc.open_by_key(STATS_SHEET).worksheet("Raw-Data")

    header = wks.row_values(1)
    row = [str(row_data.get(c, "")) for c in header]

    entries = wks.get("B2:C")
    existing = [i + 2 for i, entry in enumerate(entries) if entry == [row_data["Datum"], name]]
    if existing:
        row_id = max(existing)
        res = wks.get(f"R{row_id}C2:R{row_id}C{len(row)}")
        if res[0] + [''] * (len(row)-len(res[0])-1) != row[1:]:
            wks.update([row[1:]], f"R{row_id}C2:R{row_id}C{len(row)}", raw=False)
    else:
        wks.append_row(row, value_input_option=ValueInputOption.user_entered, insert_data_option=InsertDataOption.insert_rows)


if __name__ == '__main__':
    load_dotenv()
    OBSIDIAN_FOLDER = os.getenv('OBSIDIAN_FOLDER')
    STATS_NAME = os.getenv('STATS_NAME')
    STATS_SHEET = os.getenv('STATS_SHEET')

    n = NotesApi(OBSIDIAN_FOLDER)
    submit_day(n, STATS_NAME, (datetime.datetime.now()-datetime.timedelta(days=1)).date())
