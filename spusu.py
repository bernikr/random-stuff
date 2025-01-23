import os
import re
from base64 import b64encode

import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import PKCS1_v1_5  # noqa: S413
from Crypto.PublicKey import RSA  # noqa: S413
from dotenv import load_dotenv

load_dotenv()
SPUSU_PHONE = os.getenv("SPUSU_PHONE")
SPUSU_PASSWORD = os.getenv("SPUSU_PASSWORD")

if __name__ == "__main__":
    s = requests.session()
    resp = s.get("https://www.spusu.at/login")

    # login not required when connected through mobile network
    if not resp.url.startswith("https://www.spusu.at/meinspusu"):
        pub_key = BeautifulSoup(resp.text, "html.parser").find(id="encryptionPublicKey").attrs["value"]
        cipher = PKCS1_v1_5.new(RSA.importKey(f"-----BEGIN PUBLIC KEY-----\n{pub_key}\n-----END PUBLIC KEY-----"))
        encrypted_password = b64encode(cipher.encrypt(SPUSU_PASSWORD.encode())).decode()
        resp = s.post(
            "https://www.spusu.at/login?al=0",
            data={
                "action": "Login",
                "pwdTan": encrypted_password,
                "username": SPUSU_PHONE,
            },
        )
    if not resp.url.startswith("https://www.spusu.at/meinspusu"):
        msg = "Login failed"
        raise Exception(msg)  # noqa: TRY002
    soup = BeautifulSoup(resp.text, "html.parser").select_one("form[name='customerform']")
    gauges = soup.find_all("div", class_="graphCircle")
    res = {}
    gauge_regex = re.compile(r"^([\d\.]+) / ([\d\.]+) (.+)$")
    units = {"Minuten": "minutes", "SMS": "sms", "GB": "base_data", "Bonus MB": "bonus_data"}
    for g in gauges:
        used, total, unit = gauge_regex.findall(g.text.strip().replace(",", "."))[0]
        used = int(used) if unit != "GB" else int(float(used) * 1000)
        total = int(total) if unit != "GB" else int(float(total) * 1000)
        res[f"{units[unit]}_used"] = used
        res[f"{units[unit]}_total"] = total
        res[f"{units[unit]}_remaining"] = total - used
    res["data_used"] = res["base_data_used"] + res["bonus_data_used"]
    res["data_total"] = res["base_data_total"] + res["bonus_data_total"]
    res["data_remaining"] = res["base_data_remaining"] + res["bonus_data_remaining"]
    res["eu_data_remaining"] = int(
        re.findall(r"Es stehen noch (\d+) Frei MB im EU Roaming zur Verfügung.", soup.text)[0],
    )
    limits = re.findall(r"([\d\.]+) € von maximal ([\d\.]+) €", soup.text.replace(",", "."))
    for (spent, limit), usage in zip(
        limits,
        ["extra_usage", "extra_data", "roaming_usage", "roaming_data"],
        strict=False,
    ):
        res[f"{usage}_spent"] = float(spent)
        res[f"{usage}_limit"] = float(limit)
    print(res)
