import os
import re
from pprint import pprint

import requests
from dotenv import load_dotenv

load_dotenv()
SPUSU_PHONE = os.getenv("SPUSU_PHONE")
SPUSU_PASSWORD = os.getenv("SPUSU_PASSWORD")

default_data = {
    "OperatingSystem": "Android",
    "AppVersionCode": "36",
    "AppFlavour": "spusu",
}

if __name__ == "__main__":
    s = requests.session()
    resp = s.post(
        "https://www.spusu.at/imoscms/spusuapplogin",
        data=default_data
        | {
            "Action": "login",
            "Number": SPUSU_PHONE,
            "Pwd": SPUSU_PASSWORD,
        },
    )
    if resp.status_code != 200:  # noqa: PLR2004
        msg = "Login failed"
        raise Exception(msg)  # noqa: TRY002
    tariff_id = resp.json()["billingTariffId"]
    resp = s.post(
        "https://www.spusu.at/imoscms/spusuappdata",
        data=default_data
        | {
            "Action": "simstatus",
        },
    )
    if resp.status_code != 200:  # noqa: PLR2004
        msg = "Couldnt get data"
        raise Exception(msg)  # noqa: TRY002
    data = resp.json()
    res = {}
    KEYS = {
        "Minuten": "minutes",
        "SMS": "sms",
        "MB": "base_data",
        "Bonus MB": "bonus_data",
        "Total Data": "data",
        "EU data": "eu_data",
        "Inland Tel. & SMS": "extra_usage",
        "Kostenlimit Daten": "extra_data",
        "Roaming Tel. & SMS": "roaming_usage",
        "Roaming Daten": "roaming_data",
    }
    normalizations = {
        "MoneyAmount": lambda x, b: round(x * (1 + b["vat"] / 100), 2),
        "KB": lambda x, _: int(round(x / 1024, 0)),
        "Seconds": lambda x, _: int(round(x / 60, 0)),
        "Events": lambda x, _: int(x),
    }
    for b in (b for bs in data["balancesByLimitUnitByTariffId"][str(tariff_id)].values() for b in bs):
        used = normalizations[b["limitUnit"]](b["usedUnits"], b)
        limit = normalizations[b["limitUnit"]](b["maxUnits"], b)
        label = KEYS[b["caption"]]
        res[f"{label}_used"] = used
        res[f"{label}_limit"] = limit
        res[f"{label}_remaining"] = limit - used

    res["data_used"] = res["base_data_used"] + res["bonus_data_used"]
    res["data_limit"] = res["base_data_limit"] + res["bonus_data_limit"]
    res["data_remaining"] = res["base_data_remaining"] + res["bonus_data_remaining"]
    res["eu_data_remaining"] = int(
        re.findall(
            r"Es stehen noch (\d+) Frei MB im EU Roaming zur Verfügung.",
            data["additionalInfoByTariffId"][str(tariff_id)][0],
        )[0],
    )

    sorting_order = {}
    for i, k in enumerate(KEYS.values()):
        sorting_order[f"{k}_used"] = i * 3
        sorting_order[f"{k}_limit"] = i * 3 + 1
        sorting_order[f"{k}_remaining"] = i * 3 + 2
    res = dict(sorted(res.items(), key=lambda x: sorting_order[x[0]]))
    pprint(res, sort_dicts=False)
