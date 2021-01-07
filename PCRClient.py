import requests
from PCRPack import *
import hashlib
import base64
import random
import logging
class PCRClient:
    def __init__(self, viewer_id):
        self.viewer_id = viewer_id
        self.request_id = ""
        self.session_id = ""
        self.urlroot = "https://le1-prod-all-gs-gzlj.bilibiligame.net/"
        self.default_headers={
            "Accept-Encoding": "gzip",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.1.1; MI 9 Build/NMF26X)",
            "X-Unity-Version": "2017.4.37c2",
            "APP-VER": "2.4.9",
            "BATTLE-LOGIC-VERSION": "3",
            "BUNDLE_VER" : "",
            "CHANNEL-ID": "1",
            "DEVICE": "2",
            "DEVICE-ID": "c8b51fe5cb8508c2941900e8eb5b3f8b",
            "DEVICE-NAME": "Xiaomi MI 9",
            "EXCEL-VER": "1.0.0",
            "GRAPHICS-DEVICE-NAME": "Adreno (TM) 540",
            "IP-ADDRESS": "172.17.100.15",
            "KEYCHAIN": "",
            "LOCALE": "CN",
            "PLATFORM": "2",
            "PLATFORM-ID": "2", 
            "PLATFORM-OS-VERSION": "Android OS 5.1.1 / API-22 (NMF26X/500200513)",
            "REGION-CODE": "",
            "RES-KEY": "ab00a0a6dd915a052a2ef7fd649083e5",
            "RES-VER": "10002200",
            "SHORT-UDID": "000a85;436;834=656=636=186A781=432?856C486@711717752186363143276147888735732",
            "Connection": "Keep-Alive"}
        self.conn = requests.session()
    def Callapi(self, apiurl, request, crypted = True):
        key = CreateKey()
        if crypted:
            request['viewer_id'] = encrypt(str(self.viewer_id), key).decode()
        else:
            request['viewer_id'] = str(self.viewer_id)
        req = Pack(request, key)
        flag = self.request_id != None and self.request_id != ''
        flag2 = self.session_id != None and self.session_id != ''
        headers = self.default_headers
        if flag: headers["REQUEST-ID"] = self.request_id
        if flag2: headers["SID"] = self.session_id
        resp = self.conn.post(url= self.urlroot + apiurl,
                        headers = headers, data = req,verify=False)
        null = None
        if crypted:
            ret = decrypt(resp.content)
        else: ret = eval(resp.content.decode())
        ret_header = ret["data_headers"]
        if "sid" in ret_header:
            if ret_header["sid"] != None and ret_header["sid"] != "":
                self.session_id = hashlib.md5((ret_header["sid"] + "c!SID!n").encode()).hexdigest()
        if "request_id" in ret_header:
            if ret_header["request_id"] != None and ret_header["request_id"] != "" and ret_header["request_id"] != self.request_id:
                self.request_id = ret_header["request_id"]
        if "viewer_id" in ret_header:
            if ret_header["viewer_id"] != None and ret_header["viewer_id"] != 0 and ret_header["viewer_id"] != self.viewer_id:
                self.viewer_id = int(ret_header["viewer_id"])
        return ret["data"]
    def login(self, uid, access_key):
        self.manifest = self.Callapi('source_ini/get_maintenance_status', {}, False)
        ver = self.manifest["required_manifest_ver"]
        logging.debug(str(self.manifest))
        self.default_headers["MANIFEST-VER"] = ver
        logging.debug(str(self.Callapi('tool/sdk_login', {"uid": uid, "access_key" : access_key, "platform" : self.default_headers["PLATFORM-ID"], "channel_id" : self.default_headers["CHANNEL-ID"]}) ))

        logging.debug(str(self.Callapi('check/game_start', {"app_type": 0, "campaign_data" : "", "campaign_user": random.randint(1, 1000000)}) ))
        logging.debug(str(self.Callapi("check/check_agreement", {}) ))
        self.Callapi("load/index", {"carrier": "HUAWEI"})
        self.Home = self.Callapi("home/index", {'message_id': 1, 'tips_id_list': [], 'is_first': 1, 'gold_history': 0})
        logging.debug(str(self.Home))



        

    
    
