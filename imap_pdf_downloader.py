import os
from pathlib import Path

from imap_tools import MailboxFolderSelectError
from imap_tools.mailbox import MailBox
from tqdm import tqdm

IMAP_SERVER = os.environ["IMAP_SERVER"]
IMAP_USER = os.environ["IMAP_USER"]
IMAP_PASS = os.environ["IMAP_PASS"]

DOWNLOAD_FOLDER = Path("./attachments")


def main() -> None:
    DOWNLOAD_FOLDER.mkdir(exist_ok=True, parents=True)

    with MailBox(IMAP_SERVER).login(IMAP_USER, IMAP_PASS) as m:  # noqa: PLR1702
        for f in m.folder.list():
            try:
                m.folder.set(f.name, readonly=True)
            except MailboxFolderSelectError:
                print(f"Can't open {f.name}")
                continue
            print(f"Processing {f.name}")
            msg_count = m.folder.status(f.name)["MESSAGES"]
            for msg in tqdm(m.fetch(), total=msg_count):
                for a in msg.attachments:
                    if a.filename.endswith(".pdf"):
                        try:
                            (DOWNLOAD_FOLDER / f"{msg.date.strftime("%Y %m %d")} {a.filename}").write_bytes(a.payload)
                        except:  # noqa: E722
                            print(f"Couldn't write {a.filename} from {msg.subject}")


if __name__ == "__main__":
    main()
