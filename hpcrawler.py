from selenium import webdriver
import json
import os
import gpxpy
import pandas as pd
import slopeMap as sm
import numpy as np

DIR_PATH = 'hp_tracks'

MAX_TRACK_LEN = 30
LEN_SPACING = 5
TICK = 0.25


def setup():
    """
    creates a firefox driver which is capable of downloading files without popups
    """
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2)  # custom location
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', 'hp_tracks')
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
    driver = webdriver.Firefox(firefox_profile=profile)
    return driver


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


def homepage(driver):
    driver.get("https://www.hikingproject.com/")


def trails_in_urls(driver, name):
    """
    return a list of urls (strings) for paths in <name> (example Israel, Italy, France...)
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


def get_page_data(driver):
    """
    gets data from a trail page in the hiking project: tracks length and track difficulty.
    """
    e = driver.find_elements_by_xpath("//div[@class='stat-block mx-1 pb-2']")[0]
    txt = e.text
    txt = txt.split()
    track_len = txt[1]
    track_dif = txt[-1]
    return track_len, track_dif


def getTick(length):
    """
    returns the tick according to the track's length supplied.
    :param length: a track's length (km)
    :return: in
    """
    ranges = np.arange(0, MAX_TRACK_LEN, LEN_SPACING)
    for i in length(ranges) - 1:
        if ranges[i] < length <= ranges[i-1]:
            return TICK * (i + 1)


def getLengthTag(trackLength):
    if trackLength % LEN_SPACING == 0:
        return trackLength // LEN_SPACING - 1
    return trackLength // LEN_SPACING


def save_data(data, index):
    for i in np.arange(MAX_TRACK_LEN // LEN_SPACING):
        path = os.path.join(DIR_PATH, 'L' + i + '_' + str(index) + '.json')
        with open(path, 'w') as f:
            json.dump(data[i], f)


def collect_data_by_url_list(driver, urls, index):
    """
    downloads gpx of given trails
    :param driver: selenium webdriver
    :param urls: list of urls of web pages in hikingproject.com
    :param index: number of state
    """
    data = [dict() for x in range(MAX_TRACK_LEN // LEN_SPACING)]

    for i in range(len(urls)):
        driver.get(urls[i])

        # get track's length and difficulty from site:
        track_len, track_dif = get_page_data(driver)

        # download gpx file:
        download_gpx = driver.find_element_by_link_text("GPX File")
        download_gpx.click()

        # open gpx file:
        gpx_file = open('test_files/cerknicko-jezero.gpx', 'r')
        gpx = gpxpy.parse(gpx_file)

        # get elevations:
        trackElev = pd.DataFrame([{'ele': p.latitude} for p in gpx.tracks[0][0].points])

        # get points array:
        points = pd.DataFrame([{'lat': p.latitude, 'lon': p.longitude, 'time': p.time}
                               for p in gpx.tracks[0][0].points])
        # compute slopes:
        tick = getTick(track_len)
        slopes = sm.computeSlope(points, trackElev, tick)

        # save track to the correct dict (according to it's length):
        len_tag = getLengthTag(track_len)
        data[len_tag][str(i) + '_' + str(index)] = [slopes, track_dif]
    save_data(data, index)


if __name__ == "__main__":

    # countries crawled so far - Australia, Brazil, France, Italy, Switzerland, South Africa, United Kingdom
    # ,'Alaska', 'Alabama', 'Illinois', 'Florida', 'Ohio', 'Rhode Island', 'Vermont'
    countries = ['Alaska', 'Alabama', 'Illinois', 'Florida', 'Ohio', 'Rhode Island', 'Vermont']
    ff_driver = setup()
    homepage(ff_driver)
    log_in(ff_driver)

    for i in range(len(countries)):
        print(countries[i])
        trail_urls = trails_in_urls(ff_driver, countries[i])
        collect_data_by_url_list(ff_driver, trail_urls, i)

    # TERMINOLOGY EXPLAINED:
    # every state has a code <i>.
    # in collect_data_by_url_list we save the tracks in dicts by length, and the dicts we save to files:
    # each dict is saved to a file under the name: "L<k>_<i>.json", where <k> represents the lengths
    # range of the tracks in the dict, cultivated in the state <i>.
    # the keys of the tracks in a dict are: "<i>_<j>". it is a string where <j> is the number of the
    # track cultivated in the state <i>.

