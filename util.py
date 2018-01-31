# -*- coding:utf-8 -*-
'''
this file contain the necessary data and function,serving as utility tool. '''

import os
import time
import collections

import pandas as pd
import requests

MAIN_URL = 'http://datacenter.mep.gov.cn/index'
HOST_URL = 'http://datacenter.mep.gov.cn:8099/ths-report/report!list.action'
HEADER = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,zh-CN;q=0.8,zh;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0',
}

PAYLOAD = {
    'CITY': '',
    'E_DATE': '',
    'V_DATE': '',
    'isdesignpatterns': 'false',
    'page.pageNo': '1',
    'queryflag': 'open',
    'xmlname': '1462259560614'
}

# several implements I have ever tried
# PROXIES_DIST = {}
# PROXIES_LiST = [{'http': 'http://' + str(ip) + ':' + port, 'https': 'http://' + str(ip) + ':' + str(port)} for ip, port
#                 in PROXIES_DIST.items()]
# PROXY_QUEUE = multiprocessing.Queue() #can serve for process communication

PROXY_QUEUE = collections.deque()  # double-end queue of Proxy(),can be used as pure data structure only.

IS_FIRST = True  # the first time call post_html?

PROXY_SITES = [  # for now we use 66ip only
    'http://www.66ip.cn/',
    'http://www.ip181.com/',
    'http://www.xicidaili.com/',
    'http://www.data5u.com/',
    'http://proxydb.net/',
]

TRY_TIMES = 15


class Proxy(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.fail_times = 0


def load_proxies(filepath='proxy.txt'):
    '''
    load proxies from filepath and add them to queue
    :param filepath: file path to read data from
    :return: None
    '''
    with open(filepath, 'r') as f:
        for line in f.readlines():  # expected format: ip:port
            if line.strip() != '':
                ip = line.split(':')[0].strip()
                port = line.split(':')[1].strip()
                proxy = Proxy(ip, port)
                PROXY_QUEUE.append(proxy)


def dump_proxies(filepath='proxy.txt'):
    '''
    save proxy queue to filepath
    :param filepath:as name indicates
    :return: None
    '''
    with open(filepath, 'w') as f:
        while PROXY_QUEUE:  # not empty
            proxy = PROXY_QUEUE.popleft()
            ip = proxy.ip
            port = proxy.port
            f.write(str(ip) + ':' + str(port) + '\n')


def get_frame(path):
    '''
    Not used for now
    :param path: a directory path which is expected to contain csv files
    :return:  a list of pd.DataFrame
    '''
    frames = []
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        if filepath.split('.')[1] == 'csv':
            try:
                frame = pd.read_csv(filepath, parse_dates=True,
                                    index_col=0)  # use the first column as index,and parse the date
                frame = frame[(frame.type == 'AQI') & (
                    frame.hour == 8)]  # retain only the rows that satisfy such conditions
                frames.append(frame)
            except Exception as e:
                print(e)
    return frames


def get_html(url, header=HEADER):
    '''
    :param url: requests url
    :param header: requests header
    :return: html if succeed,empty string otherwise
    '''
    try:
        response = requests.get(url, timeout=3)
        response.encoding = response.apparent_encoding  # important!!! deal with Chinese messy codee
        return response.text
    except Exception as e:
        print(e)
        return ''


def post_html(url, payload, header=HEADER):
    '''
    :param url: requests url
    :param payload: post parameters
    :param header: requests headers
    :return: html if succeed,empty string otherwise
    '''
    global IS_FIRST  # or you can't change it

    if IS_FIRST == True:
        IS_FIRST = False
        load_proxies()
    if len(PROXY_QUEUE) < 3:  # not enough proxies
        os.system("python3 proxy.py")  # to crawl proxies
        load_proxies()

    success = False
    try_times = 0
    while not success:
        try_times += 1
        if try_times == TRY_TIMES:
            print('%s times failed!' % TRY_TIMES)
            break
        elif PROXY_QUEUE:
            # print('len:', len(PROXY_QUEUE))
            proxy = PROXY_QUEUE.popleft()
            proxy_tmp = {'http': 'http://' + str(proxy.ip) + ':' + proxy.port,
                         'https': 'http://' + str(proxy.ip) + ':' + str(proxy.port)}
            # print(proxy_tmp)
            try:
                response = requests.post(url, data=payload, headers=header, proxies=proxy_tmp, timeout=3)
                time.sleep(0.1)
                if response.status_code == 200:
                    # success = True
                    response.encoding = response.apparent_encoding  # important!!! deal with Chinese messy codee
                    return response.text
                else:
                    proxy.fail_times += 1
            except Exception as e:
                proxy.fail_times += 1
            finally:
                if proxy.fail_times < 2:
                    PROXY_QUEUE.append(proxy)
                else:
                    print('Deleted!')

    return ''  # return empty string


if __name__ == '__main__':
    print('This file should not be executed!')
