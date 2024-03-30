# source: https://www.52pojie.cn/thread-1880212-1-1.html
import requests
import json
import time
import datetime
import re
import random
from PIL import Image
import os


class QqQun(object):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/73.0.3683.75 Safari/537.36',
        'referer': 'https://qun.qq.com/member.html',
        'origin': 'https://qun.qq.com'
    }

    def __init__(self):
        self.bkn = None
        self.qun = None
        self.token = None
        self.qrsig = None
        self.cookies = None
        self.skey = None

    def login(self):
        if os.path.exists('cookie.txt'):
            with open('cookie.txt', 'r') as f:
                cookies = f.read().replace("'", '"')
            d = json.loads(cookies)
            self.cookies = d
            self.skey = d.get('skey')
            self.get_bkn()
            url = 'https://qun.qq.com/cgi-bin/qun_mgr/get_group_list'
            data = {'bkn': self.bkn}
            r = requests.post(url, headers=self.headers, data=data, cookies=self.cookies)
            js_data = json.loads(r.content.decode())
            if js_data.get('ec') == 4:
                print('cookie已过期，需要重新扫码')
                self.img_get()
            elif js_data.get('ec') == 0:
                print('登入成功')
                self.find_qun()
            else:
                print('出现了一点小状况....')
        else:
            print('第一次用吧？来来来，扫个码')
            self.img_get()

    def get_bkn(self):
        e = str(self.skey)
        t = 5381
        n = 0
        o = len(e)
        while n < o:
            t += (t << 5) + ord(e[n])
            n += 1
        self.bkn = t & 2147483647

    def get_token(self):
        n = len(self.qrsig)
        i = 0
        e = 0
        while n > i:
            e += (e << 5) + ord(self.qrsig[i])
            i += 1
        self.token = 2147483647 & e

    # 二维码图片
    def img_get(self):
        url = 'https://ssl.ptlogin2.qq.com/ptqrshow?'
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
        r = requests.get(url, params=params)
        qrsig = requests.utils.dict_from_cookiejar(r.cookies).get('qrsig')
        with open('qr.jpg', 'wb') as f:
            f.write(r.content)
        r.close()
        img = Image.open('qr.jpg')
        img = img.resize((350, 350))
        img.show()
        self.qrsig = qrsig
        self.get_token()
        self.get_state()

    # 扫码状态
    def get_state(self):
        while True:
            url = 'https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqun.qq.com%2Fmanage.html%23click&ptqrtoken=' + str(
                self.token) + '&ptredirect=1&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-' + str(
                time.time()) + '&js_ver=20032614&js_type=1&login_sig=&pt_uistyle=40&aid=715030901&daid=73&'
            cookies = {'qrsig': self.qrsig}
            r = requests.get(url, cookies=cookies)
            r1 = r.text
            if '二维码未失效' in r1:
                print('二维码未失效', time.strftime('%Y-%m-%d %H:%M:%S'))
            elif '二维码认证中' in r1:
                print('二维码认证中', time.strftime('%Y-%m-%d %H:%M:%S'))
            elif '二维码已失效' in r1:
                print('二维码已失效', time.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                print('登录成功', time.strftime('%Y-%m-%d %H:%M:%S'))
                os.remove('qr.jpg')
                cookies = requests.utils.dict_from_cookiejar(r.cookies)
                uin = requests.utils.dict_from_cookiejar(r.cookies).get('uin')
                regex = re.compile(r'ptsigx=(.*?)&')
                sigx = re.findall(regex, r.text)[0]
                url = 'https://ptlogin2.qun.qq.com/check_sig?pttype=1&uin=' + uin + '&service=ptqrlogin&nodirect=0' \
                                                                                    '&ptsigx=' + sigx + \
                      '&s_url=https%3A%2F%2Fqun.qq.com%2Fmanage.html&f_url=&ptlang=2052&ptredirect=101&aid=715030901' \
                      '&daid=73&j_later=0&low_login_hour=0&#174;master=0&pt_login_type=3&pt_aid=0&pt_aaid=16&pt_light=0' \
                      '&pt_3rd_aid=0 '
                r2 = requests.get(url, cookies=cookies, allow_redirects=False)
                self.cookies = requests.utils.dict_from_cookiejar(r2.cookies)
                with open('cookie.txt', 'w') as f:
                    f.write(str(self.cookies))
                self.skey = requests.utils.dict_from_cookiejar(r2.cookies).get('skey')
                self.get_bkn()
                self.find_qun()
                r.close()
                r2.close()
                break
            time.sleep(3)

    # 时间戳转时间
    def get_time(self, t):
        timeValue = time.localtime(t)
        tempDate = time.strftime("%Y-%m-%d %H:%M:%S", timeValue)
        tm = datetime.datetime.strptime(tempDate, "%Y-%m-%d %H:%M:%S")
        return tm

    # 修改群成员名称
    def revise_card(self):
        url = 'https://qun.qq.com/cgi-bin/qun_mgr/set_group_card'
        qq = input('请输入你要修改的群成员QQ:')
        msg = input('请输入修改后的群昵称:')
        data = {
            'gc': self.qun,
            'u': qq,
            'name': msg,
            'bkn': self.bkn
        }
        r = requests.post(url, headers=self.headers, data=data, cookies=self.cookies)
        js_data = json.loads(r.content.decode())
        print('不出意外的话应该修改成功了！(如果你是管理的话)')
        r.close()

    # 一个到三个月未发言的群员
    def inactive(self):
        url = 'https://qun.qq.com/cgi-bin/qun_mgr/search_group_members'
        data = {
            'gc': self.qun,
            'st': 0,
            'end': 20,
            'sort': 0,
            'last_speak_time': '2592000 | 7776000',
            'bkn': self.bkn
        }
        r = requests.post(url, headers=self.headers, data=data, cookies=self.cookies)
        js_data = json.loads(r.content.decode())
        r.close()
        if js_data.get('mems') == None:
            print('未发现一个月到三个月未发言的群成员')
        else:
            qq_list = []
            print('------以下为一个月到三个月未发言的群成员(一次显示最多20个)------')
            for i in js_data.get('mems'):
                t = self.get_time(int(i['join_time']))
                t1 = self.get_time(int(i['last_speak_time']))
                qq_list.append(i['uin'])
                print(f"QQ号:{i['uin']}\t群名称:{i['card']}\t入群时间:{t}\t最后发言:{t1}")
            while True:
                choose = input('是否要全部踢出群(y/n):')
                if choose == 'y':
                    print('收到，您选择y，程序开始执行....')
                    for qq in qq_list:
                        self.del_qq(qq)
                    print('程序执行完毕，建议重新查询不活跃群成员(一次最多只显示20人)')
                    break
                elif choose == 'n':
                    print('收到，您选择n，不踢出群')
                    break
                else:
                    print('只能输入y或者n')

    # 查看群
    def find_qun(self):
        url = 'https://qun.qq.com/cgi-bin/qun_mgr/get_group_list'
        data = {'bkn': self.bkn}
        r = requests.post(url, headers=self.headers, data=data, cookies=self.cookies)
        js_data = json.loads(r.content.decode())
        qun_list = []
        data_list = []
        if js_data.get('create') is not None:
            data_list.extend(js_data['create'])
        if js_data.get('manage') is not None:
            data_list.extend(js_data['manage'])
        if js_data.get('join') is not None:
            data_list.extend(js_data['join'])
        for x, i in enumerate(data_list, 1):
            qun_list.append(i['gc'])
            print(f"{x}.群号:{i['gc']}\t群名称:{i['gn']}\t群主:{i['owner']}")
        r.close()  # 关闭访问
        while True:
            qun = int(input('请输入需要操作的群(填序号):'))
            if qun <= len(qun_list):
                self.qun = qun_list[qun - 1]
                print(f'操作群:{qun_list[qun - 1]}')
                self.main()
                break
            else:
                print('是不是群号输错了？')

    # 查找群成员
    def find_qun_members(self):
        msg = input('请输入搜索的关键字(QQ号/昵称)：')
        url = 'https://qun.qq.com/cgi-bin/qun_mgr/search_group_members'
        data = {
            'gc': self.qun,
            'key': msg,
            'bkn': self.bkn
        }
        r = requests.post(url, headers=self.headers, data=data, cookies=self.cookies)
        js_data = json.loads(r.content.decode())
        if 'mems' in js_data:
            jd = js_data['mems'][0]
            t = self.get_time(int(jd['join_time']))
            t1 = self.get_time(int(jd['last_speak_time']))
            print(f"QQ号:{jd['uin']}\t群名称:{jd['card']}\t入群时间:{t}\t最后发言:{t1}")
        else:
            print('没有符合筛选条件的群成员')
        r.close()

    # 踢人
    def del_qq(self, qq):
        url = 'https://qun.qq.com/cgi-bin/qun_mgr/delete_group_member'
        data = {
            'gc': self.qun,
            'ul': qq,
            'flag': '0',
            'bkn': self.bkn
        }
        r = requests.post(url, headers=self.headers, data=data, cookies=self.cookies)
        js_data = json.loads(r.content.decode())
        if js_data['ec'] == 0:
            if 'ul' in js_data:
                print(f'已将QQ{js_data["ul"][0]}踢出本群！')
            else:
                print(f'QQ[{qq}]地位与你同级或大于你的权限，无法进行操作！')
        else:
            print(f'未在本群查找到此{qq}')
        r.close()

    def main(self):
        while True:
            print("""
            ---注意:有些需要管理员或者群主权限---
            1.查找群成员
            2.移除群成员
            3.查看不活跃群员
            4.修改群昵称
            5.切换群
            6.退出系统
            """)
            choose = input('请选择操作序号：')
            if choose == '1':
                self.find_qun_members()
                input('按回车键继续操作......')
            elif choose == '2':
                qq = input('请输入要操作的QQ号：')
                self.del_qq(qq)
                input('按回车键继续操作......')
            elif choose == '3':
                self.inactive()
                input('按回车键继续操作......')
            elif choose == '4':
                self.revise_card()
                input('按回车键继续操作......')
            elif choose == '5':
                self.find_qun()
            elif choose == '6':
                print('欢迎下次使用')
                break
            else:
                print('请输入正确的序号!')


if __name__ == '__main__':
    q = QqQun()
    q.login()
