import csv
import json
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

APPLIST_FOLDER = Path(os.getenv("APPLIST_FOLDER", ""))
OPTAINIUM_FOLDER = Path(os.getenv("OPTAINIUM_FOLDER", ""))

if __name__ == "__main__":
    file = max(APPLIST_FOLDER.glob("*.csv"), key=lambda x: x.stem)
    with file.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        apps = [a for a in r if a["System"] == "false" and a["Install source"] == "Google Play Store"]

    opt_file = max(OPTAINIUM_FOLDER.glob("*.json"), key=lambda x: x.stem)
    with opt_file.open(encoding="utf-8") as f:
        opt = json.load(f)
    opt_ids = {x["id"] for x in opt["apps"]}
    apps = [a for a in apps if a["Package"] not in opt_ids]

    urls = []
    for app in tqdm(apps):
        res = requests.get(f"https://apkpure.net/-/{app['Package']}/versions", timeout=10)
        if res.status_code != requests.codes.ok:
            print(f"App {app['Name']} not found on apkpure")
            continue
        s = BeautifulSoup(res.text, "html.parser")
        avaible_version = int(
            s.select_one("ul.version-list li:first-child div.version-info a").attrs["data-dt-version-code"],  # type: ignore
        )
        installed_version = int(app["Version"].split("(")[-1].split(")")[0])
        if avaible_version < installed_version:
            print(f"App {app['Name']} is outdated")
            continue
        urls.append(res.url)
    (APPLIST_FOLDER / f"{file.stem}.apkpure.txt").write_text("\n".join(urls), newline="\n")
