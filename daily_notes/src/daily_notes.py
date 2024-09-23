import datetime
import json
from enum import Enum, auto
from pathlib import Path
from typing import TextIO

import yaml
from moment import moment


def dict_merge(x, y, prefer_right=False):
    if not isinstance(x, dict) or not isinstance(y, dict):
        return y if prefer_right else x
    z = {}
    overlapping_keys = x.keys() & y.keys()
    for key in x.keys():
        if key in overlapping_keys:
            z[key] = dict_merge(x[key], y[key], prefer_right)
        else:
            z[key] = x[key]
    for key in y.keys() - overlapping_keys:
        z[key] = y[key]
    return z


def load_note(f: TextIO) -> tuple[str, dict[str, any]]:
    f = f.read()
    if f[0:4] != "---\n":
        return f, {}
    _, header, content = f.split('---\n', 2)
    data = yaml.safe_load(header)
    return content, data


def dump_note(f: TextIO, content: str, data: dict[str, any], file=None) -> None:
    f.write('---\n')
    f.write(yaml.dump(data, default_flow_style=False, sort_keys=False))
    f.write('---\n')
    f.write(content)


class CreateMode(Enum):
    IGNORE = auto()
    EMPTY = auto()
    TEMPLATE = auto()


class NotesApi:
    folder: Path = None
    config = None

    def __init__(self, notes_folder: Path | str):
        self.folder = Path(notes_folder)
        config_file = self.folder / '.obsidian/daily-notes.json'
        if not config_file.is_file():
            raise IOError('Could not find Daily Notes config')
        self.config = json.loads(config_file.read_text())

    @property
    def daily_folder(self):
        return self.folder / self.config['folder']

    def _get_file(self, date: datetime.date, create: CreateMode = CreateMode.IGNORE) -> Path:
        file = self.daily_folder / f"{moment(date.isoformat()).format(self.config['format'])}.md"
        if not file.is_file():
            match create:
                case CreateMode.IGNORE:
                    pass
                case CreateMode.TEMPLATE:
                    file.write_text((self.folder / f"{self.config['template']}.md").read_text())
                case CreateMode.EMPTY:
                    file.touch()
                case _:
                    raise NotImplementedError()
        return file

    def get_data(self, date: datetime.date) -> dict[str, any]:
        file = self._get_file(date)
        if not file.is_file():
            return {}
        with file.open() as f:
            note, meta = load_note(f)
        return meta

    def add_data(self, date: datetime.date, data: dict[str, any], overwrite: bool = False,
                 create: CreateMode = CreateMode.IGNORE) -> bool:
        file = self._get_file(date, create)
        if not file.is_file():
            return False
        with file.open("r+") as f:
            note, note_data = load_note(f)
            note_data = dict_merge(note_data, data, overwrite)
            f.seek(0)
            dump_note(f, note, note_data)
        return True
