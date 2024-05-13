import os
import re
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()
HOT_PHONE = os.getenv('HOT_PHONE')
HOT_PUK1 = os.getenv('HOT_PUK1')

if __name__ == '__main__':
    s = requests.session()
    resp = s.post("https://www.hot.at/api/?Mode=Selfcare&Function=LoginPuk", data={"Msisdn": HOT_PHONE, "Puk": HOT_PUK1}).json()

    resp = s.get("https://www.hot.at/selfcare/").text
    csrf = re.findall(r"\"CSRFToken\":\s*\"([a-zA-z0-9]+)\"", resp)

    result = {}

    resp = s.get("https://www.hot.at/api/?Mode=Selfcare&Function=getHeaderBox", headers={"CSRFToken": csrf[0]}).json()
    result['remaining'] = resp['Result']['Tariff']['Units'][0]['Available']
    result['total'] = resp['Result']['Tariff']['Units'][0]['Included']
    result['to_date'] = datetime.strptime(resp['Result']['Tariff']['ToDate'], '%d.%m.%Y').date()

    resp = s.get("https://www.hot.at/api/?Mode=Selfcare&Function=getBalance", headers={"CSRFToken": csrf[0]}).json()
    result['balance'] = resp['Result']['Balance']
    result['deactivation_date'] = datetime.strptime(resp['Result']['DeactivationDate'], '%d.%m.%Y').date()
    print(result)

