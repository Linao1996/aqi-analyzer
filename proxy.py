# -*- coding:utf-8 -*-
from multiprocessing.pool import Pool
import requests
from bs4 import BeautifulSoup
import util


def test_proxy(proxy):
    '''
    test proxy
    :param proxy: Dist of format {'http':'https://ip:port','https':'http://ip:port'}
    :return: Boolean value,True if the proxy works
    '''
    try:
        if requests.get(util.MAIN_URL, proxies=proxy, timeout=2).status_code == 200:
            # print('success!')
            print(proxy)
            return True
        else:
            # print('failed!')
            return False
    except Exception as e:
        # print('failed!')
        return False


def get_proxies_66(site=util.PROXY_SITES[0], filepath='proxy.txt'):
    '''
    crawl and test proxy from 66ip and save it to file
    :param site: proxy site(66ip)
    :return: None
    '''
    print('start crawl proxies:')
    soup = BeautifulSoup(util.get_html(site, header=util.HEADER), 'lxml')
    tbs = soup.find_all('table')[2]
    trs = tbs.find_all('tr')[1:]
    for tr in trs:
        ip = tr.find_all('td')[0].text
        port = tr.find_all('td')[1].text
        proxy_value = 'http:' + str(ip) + ':' + str(port)
        proxy = {
            'http': proxy_value,
            'https': proxy_value
        }
        if test_proxy(proxy):
            with open(filepath, 'a+') as f:
                f.write(str(ip) + ':' + str(port) + '\n')


def crawl_proxies(pagenum=5):
    '''
    crawl proxies and save as json file
    :param filepath: json file path to load
    :param pagenum: number of proxy pages to crawl
    :return: None
    '''
    urls = [util.PROXY_SITES[0] + str(i) + '.html' for i in range(1, pagenum)]
    print('enter proxy-crawler pool:')
    pool = Pool(5)
    pool.map(get_proxies_66, urls)
    pool.close()
    pool.join()


# def serilize_proxy_queue():
#     with open('proxy.txt', 'rb') as f:
#         util.PROXY_QUEUE = pickle.load(f)

if __name__=='__main__':
    print('start execute proxy.py:')
    crawl_proxies(pagenum=20)
