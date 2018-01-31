# -*- coding:utf-8 -*-
import sys
from  datetime import datetime
import util
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd


def year_input():
    '''
    get and modify parameter from command line
    :return: None
    '''
    if len(sys.argv) == 3:
        city = sys.argv[1]
        year = sys.argv[2]
        util.PAYLOAD['CITY'] = city
        util.PAYLOAD['E_DATE'] = year + '-12-31'
        util.PAYLOAD['V_DATE'] = year + '-01-01'


def get_year_dataframe(html):
    '''
    :param html: html string to be parsed
    :return: a pandas.DataFrame object that contains AQI information
    '''
    result = {}
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find_all('table', attrs={'class': 'report-table'})[0]
    trs = table.find_all('tr')
    rownum = len(trs)
    if rownum == 1:
        return
    ths = trs[0].find_all('th')
    tds = trs[1].find_all('td')
    for th, td in zip(ths, tds):
        result[th.text] = [td.text]
    for i in range(2, rownum):
        tds = trs[i].find_all('td')
        for th, td in zip(ths, tds):
            result[th.text].append(td.text)  # result:{'xx':[],'yy':[]}
    obj = pd.DataFrame(result, columns=['日期', '城市', 'AQI指数', '空气质量级别', '首要污染物'])
    return obj.set_index('日期')  # using certain column as index


def form_frame(city, year):
    '''
    :param city: city to be inquired
    :param year:  year to be inquired
    :return:  a pandas.DataFrame
    '''
    util.PAYLOAD['CITY'] = city
    util.PAYLOAD['V_DATE'] = year + '-01-01'
    util.PAYLOAD['E_DATE'] = year + '-12-31'
    frames = []
    for i in range(1, 14):
        util.PAYLOAD['page.pageNo'] = i
        print('pagenum: %s' % i)
        try:
            html = util.post_html(util.HOST_URL, util.PAYLOAD, util.HEADER)
            frames.append(get_year_dataframe(html))
        except Exception as e:
            print('Exception: %s' % e)
            # return pd.concat(frames).sort_index()
    return pd.concat(frames).sort_index()  # concat dataframes using columns


def get_date_list(frame):
    '''
    :param frame: DataFrame which use date as index
    :return: a list of date of format '%Y-%m-%d'
    '''
    dti = pd.date_range(frame.index[0], frame.index[-1], freq='m')  # m means month
    array = dti.to_pydatetime()
    date_only_array = np.vectorize(lambda s: s.strftime('%Y-%m-%d'))(
        array)  # np.vectorize(lambda ...) is a function,using every elements in array as parameter for it,and return a numpy array
    return date_only_array


def plot_file_year(filepath='data.csv'):
    '''
    draw and save plot,reading data from filepath
    :param filepath: data file path
    :return: None
    '''
    zh = FontProperties(fname='/usr/share/fonts/msyh.ttf')  # to display Chinese properly
    frame = pd.read_csv(filepath, index_col=0)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(frame[u'AQI指数'], 'b-', linewidth=1, alpha=0.5)
    ax.set_xticks(get_date_list(frame))
    ax.set_xticklabels([x[5:] for x in get_date_list(frame)], rotation=30)  # mm-dd
    city = frame[u'城市'].values[0]
    year = frame.index[0][:4]
    ax.set_title(u'AQI index of %s in %s' % (city, year), fontproperties=zh,color = 'red')
    plt.savefig('report/%s %s _plot.png' % (year, city))
    plt.show()


# plot_file_year()


def get_plot(city, year):
    form_frame(city, year).to_csv('data.csv')
    plot_file_year('data.csv')


def pie_file_of_months(filepath):
    '''
    draw and save a chart of 12 subplot,each of which is a pie chart of the number of days of each pollution grade
    :param filepath: path to read data from
    :return: None
    '''
    zh = FontProperties(fname='/usr/share/fonts/msyh.ttf')
    fig, axes = plt.subplots(3, 4)
    frame = pd.read_csv('data.csv', index_col=0)
    get_month = lambda x: datetime.strptime(x, '%Y-%m-%d').month
    frame['month'] = [get_month(x) for x in frame.index]
    grouped = frame.groupby(['month', '空气质量级别'])
    grade_frame = grouped.size().unstack().fillna(0)[['优', '良', '轻度污染', '中度污染', '重度污染']]
    colors = ['skyblue', 'green', 'gold', 'red', 'purple']
    labels = ['优', '良', '轻度污染', '中度污染', '重度污染']
    month = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    explode = (0, 0, 0, 0.2, 0.2)
    pie = None
    for i in range(12):
        li = [x / grade_frame.iloc[i].sum() for x in list(grade_frame.iloc[i])]
        pie = axes.flat[i].pie(li, explode=explode, colors=colors, shadow=True, startangle=90, autopct='%3.1f%%',
                               pctdistance=0.8)
        axes.flat[i].set_title(month[i], fontproperties=zh)
    # plt.set_title()
    city = frame[u'城市'].values[0]
    year = frame.index[1][:4]
    fig.suptitle(u' %s %s 年空气质量报告' % (city, year), fontproperties=zh, color='red')
    plt.subplots_adjust(left=0.0, bottom=0.1, right=0.85)
    plt.legend(pie[0], pie[1], labels=labels, prop=zh, bbox_to_anchor=(1.5, 3.5))
    plt.savefig('report/%s %s _pie_months.png' % (year, city))
    # plt.tight_layout()


def get_pie_of_months(city, year):
    form_frame(city, year).to_csv('data.csv')
    pie_file_of_months('data.csv')


def bar_file_of_months(filepath):
    '''
    draw and save a bar chart of 12 subplots,each of which representing a month's primary pollutant imformation
    :param filepath: filepath to read data from
    :return: None
    '''
    frame = pd.read_csv(filepath, index_col=0)
    get_month = lambda x: datetime.strptime(x, '%Y-%m-%d').month
    frame['month'] = [get_month(x) for x in frame.index.values]
    grouped = frame.groupby(['month', '首要污染物'])
    pol_frame = grouped.size().unstack().fillna(0)
    pol_frame = pol_frame.applymap(lambda x: int(x))  # series:map
    pol_set_tmp = (set(x.split(',')) for x in pol_frame.columns.values)
    pol_set = set.union(*pol_set_tmp)  # get all names of pollutant
    pol_list = list(pol_set)
    for name in pol_frame.columns.values:
        if ',' in name:
            name1, name2 = name.split(',')
            pol_frame[name1] = pol_frame[name1] + pol_frame[name]
            pol_frame[name2] = pol_frame[name2] + pol_frame[name]
            del pol_frame[name]
    pol_frame = pol_frame[['臭氧8小时', 'PM10', 'PM2.5', 'NO2']]

    colors = ['purple', 'blue', 'green', 'red']
    month = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']

    zh = FontProperties(fname='/usr/share/fonts/msyh.ttf')  # to display Chinese properly
    fig, axes = plt.subplots(3, 4)
    x = np.arange(4)
    for i in range(12):
        axes.flat[i].bar(x, pol_frame.iloc[i].values, color=colors)
        axes.flat[i].set_title(month[i], fontproperties=zh)
        axes.flat[i].set_xticks([0, 1, 2, 3])
        axes.flat[i].set_xticklabels(['臭氧', 'PM10', 'PM2.5', 'NO2'], fontproperties=zh)
    city = frame[u'城市'].values[0]
    year = frame.index[1][:4]
    fig.suptitle('%s %s 年主要污染物统计' % (city, year), fontproperties=zh, color='red')
    plt.tight_layout()
    plt.savefig('report/%s_%s_bar_months.png' % (year, city))
    plt.show()


# bar_file('data.csv')

def get_bar_of_months(city, year):
    form_frame(city, year).to_csv('data.csv')
    bar_file_of_months('data.csv')


def pie_file_of_year(filepath):
    '''
    draw and save pie chart of each pollution grade over a year
    :param filepath:
    :return:
    '''
    frame = pd.read_csv('data.csv', index_col=0)
    grouped = frame.groupby('空气质量级别')
    grade_frame = grouped.size()[['优', '良', '轻度污染', '中度污染', '重度污染']]
    colors = ['skyblue', 'green', 'gold', 'red', 'purple']
    labels = ['优', '良', '轻度污染', '中度污染', '重度污染']
    zh = FontProperties(fname='/usr/share/fonts/msyh.ttf')
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    explode = (0, 0, 0, 0.2, 0.2)
    li = [x / grade_frame.sum() for x in list(grade_frame)]
    pie = ax.pie(li, explode=explode, labels=labels, colors=colors, shadow=True, startangle=90, autopct='%3.1f%%',
                 pctdistance=0.8)
    for font in pie[1]:
        font.set_fontproperties(zh)
    # print(pie)
    city = frame[u'城市'].values[0]
    year = frame.index[1][:4]
    ax.set_title(u' %s %s 年空气质量报告' % (city, year), fontproperties=zh, color='red')
    plt.legend(pie[0], pie[1], labels=labels, prop=zh, bbox_to_anchor=(1.5, 3.5))
    # plt.show()
    plt.savefig('report/%s %s _pie_year.png' % (year, city))
    # plt.tight_layout()     # get_bar('北京','2017')


def get_pie_of_year(city, year):
    form_frame(city, year).to_csv('data.csv')
    pie_file_of_year('data.csv')


util.dump_proxies()
