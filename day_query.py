# -*- coding:utf-8 -*-
'''
return the result of pollution information of certain city and day
'''
import sys
import util
from bs4 import BeautifulSoup
import pandas as pd
import re


def day_input():
    if len(sys.argv) == 3:
        city = sys.argv[1]
        date = sys.argv[2]
        util.PAYLOAD['CITY'] = city
        util.PAYLOAD['E_DATE'] = date
        util.PAYLOAD['V_DATE'] = date



def get_day_data(html):
    '''
    :param html: html string to be parsed
    :return: a pandas.Series object that contains AQI information
    '''
    result = {}
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find_all('table', attrs={'class': 'report-table'})[0]
    ths = table.find_all('th')
    tds = table.find_all('td')
    for th, td in zip(ths, tds):  # this usage is common
        result[th.text] = td.text
    obj = pd.Series(result)  # using dict to get a pandas.Series object
    obj = obj[['日期', '城市', 'AQI指数', '空气质量级别', '首要污染物']]  # retain only some of the columns
    return obj


def re_input():
    util.PAYLOAD['CITY'] = input('city:')
    date = input('date:')
    util.PAYLOAD['E_DATE'] = date
    util.PAYLOAD['V_DATE'] = date


is_first = True


def test_input():
    global is_first
    date = util.PAYLOAD['E_DATE']
    m = re.match(r'^(\d{4})\-(\d{1,2})\-(\d{1,2})', date)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        if year < 2014 or year > 2018 or month < 1 or month > 12 or day < 1 or day > 31:
            print('wrong date range!(only support query after 2014')
            return False
        return True
    elif is_first:
        is_first = False
        print('please input city and date: (date format:YYYY-mm-dd)')
        return False

    else:
        print("wrong input format! city YYYY-mm-dd")
        return False


if __name__ == '__main__':
    day_input()
    if not test_input():
        re_input()
    html = util.post_html(util.HOST_URL, util.PAYLOAD, util.HEADER)
    result = get_day_data(html)
    print(result)
