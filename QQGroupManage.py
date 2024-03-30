import json
import random
import re
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image


class QQGroupManage:
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/73.0.3683.75 Safari/537.36',
        'referer': 'https://qun.qq.com/member.html',
        'origin': 'https://qun.qq.com'
    }

    def __init__(self):
        self.qr_sig: str = None
        self.qr_token: int = None
        self.sig_skey: str = None
        self.sig_bkn: int = None
        self.cookies: dict = None
        self.session = requests.session()

    def login(self):
        if Path('cookie.json').exists():
            with open('cookie.json', 'r') as f:
                self.cookies = json.load(f)
            self.sig_skey = self.cookies.get('skey')
            self.sig_bkn = self.calc_bkn(self.sig_skey)
            self.session.cookies.update(self.cookies)
            self.session.headers.update(self.headers)
            if not self.get_login_expired():
                print('登录成功...')
                return

        qr_bytes = self.get_login_qr()
        img = Image.open(BytesIO(qr_bytes))
        img = img.resize((300, 300))
        img.show()

        self.cookies = self.get_login_state()
        with open('cookie.json', 'w') as f:
            json.dump(self.cookies, f)

    @staticmethod
    def calc_qr_token(qr_sig: str) -> int:
        e = 0
        for char in qr_sig:
            e += (e << 5) + ord(char)
        return e & 0x7FFFFFFF

    @staticmethod
    def calc_bkn(skey: str) -> int:
        t = 5381
        for char in skey:
            t += (t << 5) + ord(char)
        return t & 0x7FFFFFFF

    def get_login_qr(self) -> bytes:
        """
        获取QR登录二维码

        :return: 二维码图片的bytes
        """
        url = 'https://ssl.ptlogin2.qq.com/ptqrshow'
        params = {
            'appid': '715030901',
            'e': '2',
            'l': 'M',
            's': '3',
            'd': '72',
            'v': '4',
            't': random.random(),
            'daid': '73',
            'pt_3rd_aid': '0'
        }

        with self.session.get(url, params=params) as r:
            r.raise_for_status()  # 如果请求失败会抛出异常
            self.qr_sig = r.cookies.get('qrsig')
            self.qr_token = self.calc_qr_token(self.qr_sig)
            return r.content

    def get_login_state(self) -> dict:
        """
        获取QR登录状态, 依赖`get_login_qr`函数

        :return: 登录后的cookies(dict)
        """
        url_state = 'https://ssl.ptlogin2.qq.com/ptqrlogin'
        params_state = {
            'u1': 'https://qun.qq.com/manage.html#click',
            'ptqrtoken': str(self.qr_token),
            'ptredirect': '1',
            'h': '1',
            't': '1',
            'g': '1',
            'from_ui': '1',
            'ptlang': '2052',
            # 'action': '0-0-' + str(time.time()),
            'js_ver': '20032614',
            'js_type': '1',
            'login_sig': '',
            'pt_uistyle': '40',
            'aid': '715030901',
            'daid': '73'
        }
        while True:
            params_state['action'] = '0-0-' + str(time.time())
            with self.session.get(url_state, params=params_state) as r:
                r.raise_for_status()
                text = r.text
                cookies = r.cookies

            if '二维码未失效' in text:
                print(f'二维码未失效, {time.strftime('%Y-%m-%d %H:%M:%S')}')
            elif '二维码认证中' in text:
                print(f'二维码认证中, {time.strftime('%Y-%m-%d %H:%M:%S')}')
            elif '二维码已失效' in text:
                print(f'二维码已失效, {time.strftime('%Y-%m-%d %H:%M:%S')}')
                return None
            elif '登录成功' in text:
                print(f'登录成功, {time.strftime('%Y-%m-%d %H:%M:%S')}')
                uin = cookies.get('uin')
                sigx = re.findall(r'ptsigx=(.*?)&', text)[0]
                break

            time.sleep(2)

        url_sig = 'https://ptlogin2.qun.qq.com/check_sig'
        params_sig = {
            'pttype': '1',
            'uin': uin,
            'service': 'ptqrlogin',
            'nodirect': '0',
            'ptsigx': sigx,
            's_url': 'https://qun.qq.com/manage.html',
            'f_url': '',
            'ptlang': '2052',
            'ptredirect': '101',
            'aid': '715030901',
            'daid': '73',
            'j_later': '0',
            'low_login_hour': '0',
            '®master': '0',
            'pt_login_type': '3',
            'pt_aid': '0',
            'pt_aaid': '16',
            'pt_light': '0',
            'pt_3rd_aid': '0'
        }
        with self.session.get(url_sig, params=params_sig,
                              allow_redirects=False) as r:
            r.raise_for_status()
            cookies = r.cookies
            self.sig_skey = cookies.get('skey')
            self.sig_bkn = self.calc_bkn(self.sig_skey)
            return dict(cookies)

    def get_login_expired(self) -> bool:
        """
        检查登录是否过期

        :return: 是否过期
        """
        url = 'https://qun.qq.com/cgi-bin/qun_mgr/get_group_list'
        data = {'bkn': self.sig_bkn}
        with self.session.post(url, data=data) as r:
            r.raise_for_status()
            return r.json().get('ec') != 0

    def get_group_list(self):
        """
        获取群列表, 依赖`login`函数

        :return:
        """
        url = 'https://qun.qq.com/cgi-bin/qun_mgr/get_group_list'
        data = {'bkn': self.sig_bkn}
        with self.session.post(url, data=data) as r:
            r.raise_for_status()
            js = r.json()

            group_create = group_manage = group_join = []
            # 格式 [{'gc': 群号, 'gn': 群名, 'owner': 群主}]
            if js.get('create'):
                group_create = js.get('create')
            if js.get('manage'):
                group_manage = js.get('manage')
            if js.get('join'):
                group_join = js.get('join')

            # 格式 [{群号: 群名}]
            group_create = [{str(g.get('gc')): g.get('gn')} for g in group_create]
            group_manage = [{str(g.get('gc')): g.get('gn')} for g in group_manage]
            group_join = [{str(g.get('gc')): g.get('gn')} for g in group_join]

            return group_create, group_manage, group_join


if __name__ == '__main__':
    qq_gm = QQGroupManage()
    qq_gm.login()

    gc, gm, gj = qq_gm.get_group_list()
    print(f'创建的群: {gc}')
    print(f'管理的群: {gm}')
    print(f'加入的群: {gj}')
