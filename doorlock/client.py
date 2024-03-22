import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .hashing import *
from .config import *
from .database import *
from .utils import *
from urllib.parse import quote


class Doorlock:
    os_type_cd = "ADR"
    os_ver = "13"

    app_ver = "2.0.33"
    api_ver = "v20"

    country_cd = "KR"

    locale = "ko_KR"
    location_agree_yn = "N"

    time_zone = 9

    def __init__(self, login_id, password):
        self.login_id = login_id
        self.password = password

        os.makedirs("./databases", exist_ok=True)

        self.database = Database(f"./databases/{self.login_id}.json")
        self.load_data()

        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def load_data(self):
        self.database.load()

        self.imei = self.database.get("imei")
        if self.imei is None:
            self.imei = generate_random_imei()
            self.database.set("imei", self.imei)

        self.auth_token = self.database.get("auth_token", "")
        self.auth_code = self.database.get("auth_code", None)
        self.member_id = self.database.get("member_id", None)

    def update_header(self, headers: dict = {}):
        headers.update(DEFAULT_HEADERS)

        headers.update({"Authorization": f"CUL {self.auth_token}"})

        if self.auth_code != None:
            headers.update({"AuthCode": f"{self.auth_code}"})

        return headers

    def get(
        self,
        url: str = "",
        headers: dict = {},
        retry: int = 0,
    ):
        if retry == 3:
            return
        try:
            headers = self.update_header(headers)

            get = self.session.get(url, headers=headers)

            if (
                get.status_code == 401
                and self.login_id != None
                and self.password != None
                and retry == 0
            ):
                self.login()
                return self.get(url, headers, retry + 1)
            return get
        except:
            self.login()
            return self.get(url, headers, retry + 1)

    def put(
        self,
        url: str = "",
        json: dict = {},
        headers: dict = {},
        retry: int = 0,
    ):
        if retry == 3:
            return
        try:
            headers = self.update_header(headers)

            json.update({"hashData": sha512("".join([str(i) for i in json.values()]))})

            put = self.session.put(url, json=json, headers=headers)

            if (
                put.status_code == 401
                and self.login_id != None
                and self.password != None
                and retry == 0
            ):
                self.login()
                return self.put(url, json, headers, retry + 1)
            return put
        except:
            self.login()
            return self.put(url, json, headers, retry + 1)

    @property
    def create_date(self):
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def login(self):
        url = "https://iot.samsung-ihp.com:8088/openhome/v10/user/login"

        headers = {
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "acceptLanguage": "ko_KR",
        }

        json_data = {
            "apiVer": self.api_ver,
            "appVer": self.app_ver,
            "authNumber": "",
            "countryCd": self.country_cd,
            "createDate": self.create_date,
            "imei": self.imei,
            "locale": self.locale,
            "locationAgreeYn": self.location_agree_yn,
            "loginId": self.login_id,
            "mobileNum": "",
            "osTypeCd": self.os_type_cd,
            "osVer": self.os_ver,
            "overwrite": True,
            "pushToken": "",
            "pwd": sha512(self.password),
            "timeZone": self.time_zone,
        }
        response = self.put(url, json=json_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.database.set("auth_token", data["authToken"])
            self.database.set("auth_code", data["authCode"])
            self.database.set("member_id", data["memberId"])
            self.load_data()

            return response.json()
        raise Exception("Login Error")

    def get_user_info(self):
        current_time_encoded = quote(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        url = f"https://iot.samsung-ihp.com:8088/openhome/v20/usermgmt/getusrinfo?memberId={self.member_id}&createDate={current_time_encoded}&hashData="

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "acceptLanguage": "ko_KR",
        }

        response = self.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        raise Exception("Error")

    def get_log(self, device_id: str):
        url = f"https://iot.samsung-ihp.com:8088/openhome/v20/doorlockctrl/inouthistory?deviceId={device_id}&memberId={self.member_id}&locale=ko_KR&createDate={self.create_date}&hashData="

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "acceptLanguage": "ko_KR",
        }

        response = self.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        raise Exception("Log Error")

    def get_status(self, index: int = 0):
        url = f"https://iot.samsung-ihp.com:8088/openhome/v20/doorlockctrl/membersdoorlocklist?createDate={self.create_date}&favoriteYn=A&hashData=&memberId={self.member_id}"

        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "acceptLanguage": "ko_KR",
        }

        response = self.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["doorlockVOList"][index]["doorlockStatusVO"]
        return

    def open_door(
        self,
        device_id: str,
        open: bool = True,
        is_security_mode: bool = False,
    ):
        url = "https://iot.samsung-ihp.com:8088/openhome/v20/doorlockctrl/open"

        json_data = {
            "createDate": self.create_date,
            "deviceId": device_id,
            "open": open,
            "isSecurityMode": is_security_mode,
            "memberId": self.member_id,
            "securityModeRptEndDt": "",
            "securityModeRptStartDt": "",
        }

        headers = {
            "Host": "iot.samsung-ihp.com:8088",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "acceptLanguage": "ko_KR",
        }

        response = self.put(url, json=json_data, headers=headers)
        if response.status_code == 200:
            return response.json()
        raise Exception("Error")
