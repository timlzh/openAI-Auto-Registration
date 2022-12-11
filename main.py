import contextlib
import os
from random import randint
from time import sleep

import requests
from seleniumwire import webdriver
import re
import httpx


from smsactivate.api import SMSActivateAPI

API_KEY = os.getenv('SMSACTIVATE_API_KEY') # Get your API key from https://sms-activate.org/en/api2
# Set proxies if you need
# PROXIES = None
PROXIES = {
    "http": "http://localhost:1082",
    "https": "http://localhost:1082"
}
# Your gmail address
GMAIL = 'itstimlzh@gmail.com'


def register(proxies, email):
    proxies_parsed = {}
    if "http" in proxies:
        proxies_parsed["http://"] = proxies["http"]
    if "https" in proxies:
        proxies_parsed["https://"] = proxies["https"]
    if "socks5" in proxies:
        proxies_parsed["socks5://"] = proxies["socks5"]
    S = httpx.Client(http2=True, verify=False, proxies=proxies_parsed)
    url = "https://auth0.openai.com/authorize?client_id=DRivsnm2Mu42T3KOpqdtwB3NYviHYzwD&audience=https%3A%2F%2Fapi.openai.com%2Fv1&redirect_uri=https%3A%2F%2Fbeta.openai.com%2Fauth%2Fcallback&max_age=0&scope=openid%20profile%20email%20offline_access&response_type=code&response_mode=query&state=Sjh0Sk1KM1pveWpGRjNsdW5pbEhRVk5qdl9fUVJGWU9Pbl9FNC5GRS5LRQ%3D%3D&nonce=c2dTR2FvbmVSfkdRVEtRMFhVXzdWcEZxS2lXbVlrS2hOQl9YTDlZaFdzeA%3D%3D&code_challenge=otkSKIblAWaBOl5FROCl6ep26sFDWKh6aeVQH_3DrEo&code_challenge_method=S256&auth0Client=eyJuYW1lIjoiYXV0aDAtc3BhLWpzIiwidmVyc2lvbiI6IjEuMjEuMCJ9"
    x = S.get(url, follow_redirects=True)
    state = re.findall(r'<input type="hidden" name="state" value="(.*?)" />', x.text)[0]
    x = S.get(f"https://auth0.openai.com/u/signup/identifier?state={state}")
    data = {"state": state, "email": email, "action": "default"}
    x = S.post(f"https://auth0.openai.com/u/signup/identifier?state={state}", data=data, follow_redirects=True)
    data = {"state": state, "strengthPolicy": "low", "complexityOptions.minLength": 8, "email": email, "password": "password", "action": "default"}
    x = S.post(f"https://auth0.openai.com/u/signup/password?state={state}", data=data, follow_redirects=True)

def verify(header, phone, proxy):
    S = requests.session()
    S.headers.update(header)
    data = {"phone_number": phone,
            "country_iso": "IN",
            "channel": "sms"}
    x = S.post('https://api.openai.com/dashboard/onboarding/phone/verify', json=data, proxies=proxy)
    print(x.text)
    return x.json()["id"]

def res_print(content, status, item):
    try:
        print(f'{content}: {status[item]}')
    except KeyError:
        print(f'Error: {status["message"]}')

def check(header, id, code, proxy):
    S = requests.session()
    S.headers.update(header)
    data = {"verification_id": id,
            "verification_code": code}
    x = S.post('https://api.openai.com/dashboard/onboarding/phone/check', json=data, proxies=proxy)
    print(x.text)

def createAccount(header, id, proxy):
    S = requests.session()
    S.headers.update(header)
    data = {"app":"api","first_name":"Xi","last_name":"JinPing","picture":"https://s.gravatar.com/avatar/35d2964fdaeaa2f973167a129fee83ed?s=480&r=pg&d=https%3A%2F%2Fcdn.auth0.com%2Favatars%2Fit.png","phone_verification_id":id,"segmentation":{"purpose":"research"}}
    x = S.post('https://api.openai.com/dashboard/onboarding/create_account', json=data, proxies=proxy)
    print(x.text)
    return {
        "orgnizationID": x.json()['orgs']['data'][0]['id'],
        "sensitiveID": x.json()['session']['sensitive_id'],
    }
    
def createAPIKey(header, sensitiveID, proxy):
    S = requests.session()
    S.headers.update(header)
    S.headers.update({"authorization": f"Bearer {sensitiveID}"})
    data = {"action": "create"}
    x = S.post('https://api.openai.com/dashboard/user/api_keys', json=data, proxies=proxy)
    print(x.text)
    return x.json()['key']['sensitive_id']

def getCode(phone):
    while True:
        with contextlib.suppress(Exception):
            activations = sa.getActiveActivations()
            res_print('Activations', activations, 'activeActivations')
            for i in activations["activeActivations"]:
                if i['phoneNumber'][2:] == phone:
                    if not i["smsCode"]:
                        sleep(2)
                        break
                    return i["smsCode"][-1]


def getNumber():
    number = sa.getNumberV2(service='dr', country=22)
    res_print('Number', number, 'phoneNumber')
    return number['phoneNumber'][2:]

if __name__ == '__main__':
    print(f'Using API key:{API_KEY}')

    sa = SMSActivateAPI(API_KEY, PROXIES)

    balance = sa.getBalance()
    res_print('Balance', balance, 'balance')

    if input("Do you want to buy a number? (Y/N)") == 'Y':
        number = getNumber()
    else:
        number = input("Enter the number:+91 ")

    options = webdriver.EdgeOptions()
    options.headless = True
    driver = webdriver.Edge(options=options)
    driver.delete_all_cookies()

    driver.proxy = PROXIES

    def getElement(driver, xpath):
        while True:
            with contextlib.suppress(Exception):
                return driver.find_element("xpath", xpath)

    mail = f"{GMAIL.split('@')[0]}+{randint(0, 999999)}@{GMAIL.split('@')[1]}"
    register(PROXIES, mail)
    while(True):
        print("Waiting for email verification...Enter Y to continue")
        if input().upper() == 'Y':
            break
        
    driver.get('https://beta.openai.com/loggedout')

    email=getElement(driver, '//*[@id="username"]')
    email.send_keys(mail)
    email.submit()

    password=getElement(driver, '//*[@id="password"]')
    password.send_keys('password')
    password.submit()

    getElement(driver, '//*[@id="root"]/div[1]/div/div[2]/form/div/div[1]/div[1]/input')
    headers = {}
    for i in driver.requests:
        if "authorization: bearer" in str(i.headers).lower():
            headers = i.headers
            break
    print(headers)
    driver.quit()
    
    id = verify(headers, number, PROXIES)
    code = getCode(number)
    print(code)
    check(headers, id, code, PROXIES)
    res = createAccount(headers, id, PROXIES)
    organizationID = res["orgnizationID"]
    print(f'Organization ID: {organizationID}')
    sensitiveID = res["sensitiveID"]
    print(f'Sensitive ID: {sensitiveID}')
    apikey = createAPIKey(headers, sensitiveID, PROXIES)
    print(f'API Key: {apikey}')
    
    print(f"""\
Registeration Complete!
-----------------------
Email: {mail}
Password: password
Organization ID: {res["orgnizationID"]}
API Key: {apikey}
-----------------------
Enjoy!
""")