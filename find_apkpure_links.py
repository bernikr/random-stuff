import csv
import json
import os
from pathlib import Path

import requests
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
        res = requests.get(
            f"https://tapi.pureapk.com/v3/get_app_his_version?package_name={app['Package']}&hl=en",
            headers={
                "Ual-Access-Businessid": "projecta",
                "Ual-Access-ProjectA": r'{"device_info":{"os_ver":"36"}}',
            },
            timeout=10,
        )
        if res.status_code != requests.codes.ok:
            print(f"App {app['Name']} not found on apkpure API")
            continue

        url = f"https://apkpure.net/-/{app['Package']}"
        res2 = requests.get(url, timeout=1)
        if res2.status_code == requests.codes.ok:
            url = res2.url

        versions = res.json()["version_list"]
        if len(versions) == 0:
            print(f"App {app['Name']} has no versions")
            continue
        v = versions[0]
        avaible_version = int(v["version_code"])
        installed_version = int(app["Version"].split("(")[-1].split(")")[0])
        if avaible_version < installed_version:
            print(
                f"App {app['Name']} is outdated (installed: {app["Version"]}, "
                f"latest: {v['version_name']} ({v['version_code']}))",
            )

        urls.append(url)
    (APPLIST_FOLDER / f"{file.stem}.apkpure.txt").write_text("\n".join(urls), newline="\n")
