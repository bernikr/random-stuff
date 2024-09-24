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


def note_data_to_row(data: dict, date: datetime.date, name: str, friends_filter: list[str] = None) -> dict:
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
        h, m = divmod(d * 60, 60)
        row["Schlaf"] = f"{h:.0f}:{m:02.0f}:00"

    if (d := data.get("shits")) is not None:
        row["Toilettengänge"] = d

    if (d := data.get("sex")) is not None:
        row["Sex"] = d

    if (d := data.get("faps")) is not None:
        row["Masturbiert"] = d

    if (d := data.get("friends-met")) is not None:
        row["Freunde getroffen"] = ", ".join((f for f in d if not friends_filter or f in friends_filter))

    if (d := data.get("sport")) is not None:
        row["Sport"] = ", ".join(d)

    if (d := data.get("activities")) is not None:
        row["Tätigkeiten"] = ", ".join(d)

    if (d := data.get("game-played")) is not None:
        row["Welches Spiel gespielt"] = d

    if (d := data.get("book-read")) is not None:
        row["Buch fertig gelesen"] = d

    if (d := data.get("watchtime")) is not None:
        h, m = divmod(d * 60, 60)
        row["Medienwatchtime"] = f"{h:.0f}:{m:02.0f}:00"

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


def submit_days(api: NotesApi, name: str, sheet: str, dates: list[datetime.date]):
    gc = gspread.service_account(filename=Path(__file__).parent.parent / "service_account.json")
    stats_file = gc.open_by_key(sheet)

    friends = stats_file.worksheet("Help-Data").col_values(5)

    data_sheet = stats_file.worksheet("Raw-Data")
    entries = data_sheet.get_all_values()
    header = entries[0]

    for date in dates:
        data = api.get_data(date)
        row_data = note_data_to_row(data, date, name, friends)

        row = [str(row_data.get(c, "")) for c in header]

        existing = [i + 1 for i, entry in enumerate(entries) if entry[1] == row_data["Datum"] and entry[2] == name]
        if existing:
            row_id = max(existing)
            existing_row = entries[row_id - 1]
            if existing_row[1:] != row[1:]:
                data_sheet.update([row[1:]], f"R{row_id}C2:R{row_id}C{len(row)}", raw=False)
        else:
            data_sheet.append_row(row, value_input_option=ValueInputOption.user_entered,
                                  insert_data_option=InsertDataOption.insert_rows)


def main():
    load_dotenv()
    OBSIDIAN_FOLDER = os.getenv('OBSIDIAN_FOLDER')
    STATS_NAME = os.getenv('STATS_NAME')
    STATS_SHEET = os.getenv('STATS_SHEET')

    n = NotesApi(OBSIDIAN_FOLDER)
    now = datetime.datetime.now()
    dates = []
    for f in n.daily_folder.glob('**/*.md'):
        mod_time = datetime.datetime.fromtimestamp(f.stat().st_mtime)
        if now - mod_time < datetime.timedelta(days=1):
            try:
                date = datetime.date.fromisoformat(f.stem)
            except ValueError:
                continue
            if date.year == 2024:
                dates.append(date)
    submit_days(n, STATS_NAME, STATS_SHEET, dates)


if __name__ == '__main__':
    main()
