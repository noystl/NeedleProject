from selenium import webdriver
import json
import os
import numpy as np


def log_in(driver):
    """
    logs into hikingproject.com
    """
    elem = driver.find_element_by_link_text("Sign In")
    elem.click()
    elem_email = driver.find_element_by_xpath("//input[@placeholder='Log in with email']")
    elem_email.clear()
    elem_email.send_keys("matan.pinkas@mail.huji.ac.il")
    elem_pw = driver.find_element_by_xpath("//input[@placeholder='Password']")
    elem_pw.clear()
    elem_pw.send_keys("313287237mM")
    elem = driver.find_elements_by_xpath("//button[@class='btn btn-primary btn-lg']")
    for e in elem:
        if e.text == "Log In":
            elem = e
    elem.click()
    return


def best_of(driver):
    """
    goes to best of page in hikingproject
    """
    elem = driver.find_element_by_link_text("Best Of")
    elem.click()


def collect_data(driver):
    """
    downloads gpx of path and writes text to data file
    """
    elems = driver.find_elements_by_xpath("//div[@class='card cdr-card']")
    url = driver.current_url
    index = len(elems)
    i = 0
    after = os.listdir('C:\\Users\\Matan Pinkas\\Documents\\tracks')
    data = {}
    
    while i < index:
        before = after
        elems[i].click()
        data2 = get_page_data(driver)
        dnld = driver.find_element_by_link_text("GPX File")
        dnld.click()
        driver.get(url)
        after = os.listdir('C:\\Users\\Matan Pinkas\\Documents\\tracks')
        change = set(after) - set(before)
        name = change.pop()
        data2['gpx name'] = name
        i += 1
        data[i] = data2
        elems = driver.find_elements_by_xpath("//div[@class='card cdr-card']")
    save_data(data)


def collect_data_by_url_list(driver, urls, data, index=0):
    """
    downloads gpx of given trails
    :param driver: selenium webdriver
    :param urls: list of urls of web pages in hikingproject.com
    :param data: a dict containing data gathered perviously
    :param index: number of trails collected before - 1
    """
    after = os.listdir('C:\\Users\\Matan Pinkas\\Documents\\tracks')
    for i in range(len(urls)):
        before = after
        driver.get(urls[i])
        page_data = get_page_data(driver)
        download_gpx = driver.find_element_by_link_text("GPX File")
        download_gpx.click()
        after = os.listdir('C:\\Users\\Matan Pinkas\\Documents\\tracks')
        change = set(after) - set(before)
        name = change.pop()
        page_data['gpx_name'] = name
        data[str(i + index)] = page_data
    return data


def save_data(data, index):
    path = 'C:\\Users\\Matan Pinkas\\Documents\\tracks\\data' + str(index) + '.json'
    with open(path, 'w') as f:
        json.dump(data, f)


def setup():
    """
    creates a firefox driver which is capable of downloading files without popups
    """
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2)  # custom location
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', 'C:\\Users\\Matan Pinkas\\Documents\\tracks')
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
    driver = webdriver.Firefox(firefox_profile=profile)
    return driver


def get_page_data(driver):
    """
    gets data from a trail page in hikingproject
     (returns list of form [name, distance(km),difficulty, features] (features is a list of string of features)
    """
    res = {}
    e = driver.find_element_by_xpath("//h1[@id='trail-title']")
    res['track name'] = e.text
    e = driver.find_elements_by_xpath("//div[@class='stat-block mx-1 pb-2']")[0]
    txt = e.text
    txt = txt.split()
    res['length (km)'] = txt[1]
    res['difficulty'] = txt[-1]
    try:
        features_element = driver.find_element_by_xpath("//span[@class='font-body pl-half']")
        features = features_element.text.split(" · ")
        res['features'] = features
    except:  # basically should only fail when a page doesnt have features
        features = []
        res['features'] = features
    return res


def homepage(driver):
    driver.get("https://www.hikingproject.com/")


def trails_in_urls(driver, name):
    """
    return a list of urls (strings) for paths in <name> (example Israel, Itay, France...)
    """
    homepage(driver)
    query = "//a[@title='" + name + "']"
    elem = driver.find_element_by_xpath(query)
    url = elem.get_attribute("href")
    driver.get(url)
    # driver is not at page with data on paths in <name>
    # loop makes page show all trails in <name>

    while True:
        try:
            show_more = driver.find_element_by_xpath("//button[@id='load-more-trails']")
            show_more.click()
        except:
            break
    trail_elements = driver.find_elements_by_xpath("//tr[@class='trail-row']")
    trail_urls = []
    for i in range(len(trail_elements)):
        trail_urls.append(trail_elements[i].get_attribute("data-href"))
    return trail_urls


if __name__ == "__main__":

    # countries crawled so far - Australia, Brazil, France, Italy, Switzerland, South Africa, United Kingdom
    # ['Alaska', 'Alabama', 'Illinois', 'Florida', 'Ohio', 'Rhode Island', 'Vermont']
    # countries = ['Alaska', 'Alabama', 'Illinois', 'Florida', 'Ohio', 'Rhode Island', 'Vermont']
    # ff_driver = setup()
    # homepage(ff_driver)
    # log_in(ff_driver)
    # with open('C:\\Users\\Matan Pinkas\\Documents\\tracks\\data.json') as f:
    #     data = json.load(f)
    # keys = data.keys()
    # index = []
    # for key in keys:
    #     index.append(int(key))
    # index = np.array(index)
    # index = np.amax(index) + 1
    # c = 0
    # for i in range(len(countries)):
    #     print(countries[i])
    #     trail_urls = trails_in_urls(ff_driver, countries[i])
    #     collect_data_by_url_list(ff_driver, trail_urls, data, index)
    #     index += len(trail_urls)
    #     c += 1
    #     save_data(data, c)

    with open('C:\\Users\\Matan Pinkas\\Documents\\tracks\\data.json') as f:
        data = json.load(f)
    res = {}
    for i in data.keys():
        for feature in data[i]['features']:
            res.setdefault(feature, 0)
            res[feature] += 1
    x = 1
