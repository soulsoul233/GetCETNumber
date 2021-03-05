import requests
import time
import hmac
import hashlib
import base64
import urllib.parse
import json
import pandas as pd

FATEA_PRED_URL = "http://pred.fateadm.com"

class TmpObj():
    def __init__(self):
        self.value = None

class Rsp():
    def __init__(self):
        self.ret_code = -1
        self.cust_val = 0.0
        self.err_msg = "succ"
        self.pred_rsp = TmpObj()

    def ParseJsonRsp(self, rsp_data):
        if rsp_data is None:
            self.err_msg = "http request failed, get rsp Nil data"
            return
        jrsp = json.loads(rsp_data)
        self.ret_code = int(jrsp["RetCode"])
        self.err_msg = jrsp["ErrMsg"]
        self.request_id = jrsp["RequestId"]
        if self.ret_code == 0:
            rslt_data = jrsp["RspData"]
            if rslt_data is not None and rslt_data != "":
                jrsp_ext = json.loads(rslt_data)
                if "cust_val" in jrsp_ext:
                    data = jrsp_ext["cust_val"]
                    self.cust_val = float(data)
                if "result" in jrsp_ext:
                    data = jrsp_ext["result"]
                    self.pred_rsp.value = data


def CalcSign(pd_id, passwd, timestamp):
    md5 = hashlib.md5()
    md5.update((timestamp + passwd).encode())
    csign = md5.hexdigest()

    md5 = hashlib.md5()
    md5.update((pd_id + timestamp + csign).encode())
    csign = md5.hexdigest()
    return csign


def CalcCardSign(cardid, cardkey, timestamp, passwd):
    md5 = hashlib.md5()
    md5.update(passwd + timestamp + cardid + cardkey)
    return md5.hexdigest()


def HttpRequest(url, body_data, img_data=""):
    rsp = Rsp()
    post_data = body_data
    files = {
        'img_data': ('img_data', img_data)
    }
    header = {
        'User-Agent': 'Mozilla/5.0',
    }
    rsp_data = requests.post(url, post_data, files=files, headers=header)
    rsp.ParseJsonRsp(rsp_data.text)
    return rsp


class FateadmApi():

    def __init__(self, app_id, app_key, pd_id, pd_key):
        self.app_id = app_id
        if app_id is None:
            self.app_id = ""
        self.app_key = app_key
        self.pd_id = pd_id
        self.pd_key = pd_key
        self.host = FATEA_PRED_URL

    def Predict(self, pred_type, img_data, head_info=""):
        tm = str(int(time.time()))
        sign = CalcSign(self.pd_id, self.pd_key, tm)
        param = {
            "user_id": self.pd_id,
            "timestamp": tm,
            "sign": sign,
            "predict_type": pred_type,
            "up_type": "mt"
        }
        if head_info is not None or head_info != "":
            param["head_info"] = head_info
        if self.app_id != "":
            asign = CalcSign(self.app_id, self.app_key, tm)
            param["appid"] = self.app_id
            param["asign"] = asign
        url = self.host + "/api/capreg"
        files = img_data
        rsp = HttpRequest(url, param, files)
        return rsp

    def PredictExtend(self, pred_type, img_data, head_info=""):
        rsp = self.Predict(pred_type, img_data, head_info)
        return rsp.pred_rsp.value


if __name__ == "__main__":

    xlsx = pd.ExcelFile('data.xlsx')
    df = pd.read_excel(xlsx, 'StudentTemplate')
    NameLine = ""
    IDNumberLine = ""
    Quantity = ""
    pd_id = ""
    pd_key = ""
    app_id = ""
    app_key = ""


    NAME = []
    ID_NUMBER = []
    data = df.values
    pred_type = "30400"
    api = FateadmApi(app_id, app_key, pd_id, pd_key)
    for i in range(0, int(Quantity), 1):
        NAME.append(data[i][int(NameLine)])
    for i in range(0, int(Quantity), 1):
        ID_NUMBER.append(data[i][int(IDNumberLine)])
    for i in range(0, int(Quantity), 1):
        CODE = "http://cet-bm.neea.edu.cn/Home/VerifyCodeImg"
        VERY = requests.get(CODE)
        COOKIE = {
            'BIGipServercet_pool':VERY.cookies['BIGipServercet_pool'],
            'ASP.NET_SessionId' : VERY.cookies['ASP.NET_SessionId']
        }
        LOGIN = "http://cet-bm.neea.edu.cn/Home/ToQueryTestTicket"
        code = api.PredictExtend(pred_type, VERY.content)
        pp = {
            'provinceCode': "36",
            'IDTypeCode': "1",
            'IDNumber': ID_NUMBER[i],
            'Name': NAME[i],
            'verificationCode': code
        }
        RESULT = requests.post(LOGIN, data=pp, cookies=COOKIE)
        print(NAME[i] + RESULT.json()['Message'])

