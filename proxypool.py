import requests
from lxml import etree

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd


def get_proxies(country='Taiwan', PhantomJs_executable_path='/usr/local/Cellar/phantomjs/2.1.1/bin/phantomjs', path_or_buf = 'proxies.csv', trskip=2, verbose = 1):
    def verbose_print(s1="", s2="", v=1):
        if v == 1:
            print(s1)
        elif v == 2:
            print(s2)
        else:
            return
    
    
    def clean_text(text):
        import re
        if text is None:
            text = ''
            return text
        
        text = text.encode('latin_1', errors='ignore').decode('utf8', errors='ignore')
        text = re.sub(r'[\t\n\r]', r'', text)
        return text
    # ################################################################################
    # step 1. use PhantomJs to get .js rendered content
    # ################################################################################
    browser = webdriver.PhantomJS(executable_path = PhantomJs_executable_path)
    browser.get('http://www.gatherproxy.com/proxylist/country/?c={}'.format(country))

    # ################################################################################
    # step 2. click "Show Full List" button to generate full proxies list
    # ################################################################################
    try:
        element = WebDriverWait(browser, 1).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="body"]/form/p/input[@type="submit" and @class="button"]')))
        verbose_print('button "Show Full List" found')

        element.click()
        verbose_print('button "Show Full List" clicked', v = verbose)
        
    except:
        verbose_print('button "Show Full List" not found', v = verbose)
        
    # ################################################################################        
    # step 3. generate selector
    # ################################################################################
    selector = etree.HTML(browser.page_source)
    verbose_print('resolve responsed page content', verbose)

    # ################################################################################
    # step 4. resolve how many pages
    # ################################################################################
    pages = selector.xpath('//div[@id="body"]/form[@id="psbform"]/div[@class="pagenavi"]/a')
    verbose_print('{} pages found'.format(len(pages)), verbose)

    # ################################################################################
    # setp 5. resolve trs for first page
    # ################################################################################
    trs = selector.xpath('//div[@class="proxy-list"]/table[@id="tblproxy"]/tbody/tr')  
    key = [clean_text(th.text) for th in trs[0].xpath('./th')]
    
    proxies_list = list()
    for tr in trs[trskip:]:
        proxies_list.append([ "" if not td.xpath('./text()') else td.xpath('./text()')[0] for td in tr.xpath('./td')])
    verbose_print('page 1 done', verbose)
    
    # ################################################################################        
    # step 6. resolve trs for the rest pages
    # ################################################################################
    for i, page in enumerate(pages, 2):

        # step 6-1. click nextpage's link
        try:
            element = WebDriverWait(browser, 1).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="body"]/form[@id="psbform"]/div[@class="pagenavi"]/a[@href="#{}"]'.format(i))))
            verbose_print('<a href=#{0}> for page {0} found'.format(i), verbose)

            element.click()
            verbose_print('<a href=#{0}> for page {0} clicked'.format(i), verbose)
        except:
            verbose_print('<a href=#{0}> for page {0} not found'.format(i), verbose)
            
        # step 6-2. resolve trs for ith page
        selector = etree.HTML(browser.page_source)
        trs = selector.xpath('//div[@class="proxy-list"]/table[@id="tblproxy"]/tbody/tr')
        for tr in trs[trskip:]:
            proxies_list.append([ "" if not td.xpath('./text()') else td.xpath('./text()')[0] for td in tr.xpath('./td')])
        verbose_print('page {} done'.format(i), verbose)

    else:
        verbose_print('total {} proxies resolved'.format(len(proxies_list)), verbose)

    # ################################################################################
    # step 7. build proxies DataFrame
    # ################################################################################
    proxies = pd.DataFrame(proxies_list, columns=key)
    verbose_print('create proxies DataFrame', verbose)
    

    # ################################################################################
    # step 8. write out proxies.csv
    # ################################################################################
    proxies.to_csv(path_or_buf = path_or_buf, index = False)
    verbose_print('write proxies to csv as "{}"'.format(path_or_buf), verbose)
    
    return proxies

def proxy_pool(df, prefix = "http://", cat=":",col_ip="Ip Address", col_port="Port"):
    proxies_list = list()
    for ip, port in zip(df[col_ip], df[col_port]):
        proxies_list.append(prefix+ip+cat+port)
               
    return proxies_list