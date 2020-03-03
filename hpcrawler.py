from selenium import webdriver
import json
import os
import gpxpy
import pandas as pd
import slopeMap as sm
import numpy as np

GPX_DIR_PATH = 'hp_gpx'
TRACKS_DIR_PATH = 'hp_tracks'

MAX_TRACK_LEN = 30
LEN_SPACING = 5
TICK = 0.25


def setup():
    """
    creates a firefox driver which is capable of downloading files without popups
    """
    print("setup")
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2)
    profile.set_preference('browser.download.manager.showWhenStarting', False)

    if not os.path.exists(GPX_DIR_PATH):
        os.makedirs(GPX_DIR_PATH)

    profile.set_preference('browser.download.dir', os.path.abspath(GPX_DIR_PATH))
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
    driver = webdriver.Firefox(firefox_profile=profile)
    return driver


def log_in(driver):
    """
    logs into hikingproject.com
    """
    print("log in")
    homepage(driver)
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
    print("homepage")
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


def get_download_file_name(before, path):
    after = os.listdir(path)
    change = set(after) - set(before)
    if len(change) == 1:
        return change.pop()


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


def get_length_tag(trackLength):
    if trackLength % LEN_SPACING == 0:
        return trackLength // LEN_SPACING - 1
    return trackLength // LEN_SPACING


def save_data(data, index):
    if not os.path.exists(TRACKS_DIR_PATH):
        os.makedirs(TRACKS_DIR_PATH)
    for i in np.arange(MAX_TRACK_LEN // LEN_SPACING):
        path = os.path.join(TRACKS_DIR_PATH, 'L' + i + '_' + str(index) + '.json')
        with open(path, 'w') as f:
            json.dump(data[i], f)


def collect_tracks_data(driver, urls, index):
    """
    downloads gpx of given trails
    :param driver: selenium webdriver
    :param urls: list of urls of web pages in hikingproject.com
    :param index: number of state
    """
    features = {}

    # saves gpx files:
    files_so_far = len([name for name in os.listdir(GPX_DIR_PATH) if os.path.isfile(name)])  # TODO
    for i in np.arange(files_so_far, len(urls) + 1):
        driver.get(urls[i])

        # get track's length and difficulty from site:
        track_len, track_dif = get_page_data(driver)

        # download gpx file:
        before = os.listdir('/home/jason/Downloads')
        driver.find_element_by_link_text("GPX File").click()
        after = os.listdir('/home/jason/Downloads')
        change = set(after) - set(before)
        filename = change.pop()

        features[i] = [filename, track_len, track_dif]
    return features


def process_tracks_data(features, index):
    data = [dict() for x in range(MAX_TRACK_LEN // LEN_SPACING)]
    points, trackElev = pd.DataFrame({}), pd.DataFrame({})

    for i in range(len(features)):
        filename, track_len, track_dif = features[i]

        # open gpx file:
        gpx_file = open(os.path.join(GPX_DIR_PATH, filename), 'r', encoding="utf8")
        gpx = gpxpy.parse(gpx_file)

        # get points array & elevations:
        for track in gpx.tracks:
            for seg in track.segments:
                points = pd.DataFrame([{'lat': p.latitude, 'lon': p.longitude, 'time': p.time} for p in seg.points])
                trackElev = pd.DataFrame([{'ele': p.latitude} for p in seg.points])

        # compute slopes:
        tick = getTick(track_len)
        slopes = sm.computeSlope(points, trackElev, tick)

        # save track to the correct dict (according to it's length):
        len_tag = get_length_tag(track_len)
        data[len_tag][str(i) + '_' + str(index)] = [slopes, track_dif]
    save_data(data, index)


if __name__ == "__main__":
    # countries crawled so far - Australia, Brazil, France, Italy, Switzerland, South Africa, United Kingdom
    # ,'Alaska', 'Alabama', 'Illinois', 'Florida', 'Ohio', 'Rhode Island', 'Vermont'
    countries = ['Australia']
    ff_driver = setup()     # create gpx folder, sets up driver
    log_in(ff_driver)

    for i in range(len(countries)):
        print(countries[i])
        trail_urls = trails_in_urls(ff_driver, countries[i])
        fs = collect_tracks_data(ff_driver, trail_urls, i)
        process_tracks_data(fs, i)

    # TERMINOLOGY EXPLAINED:
    # every state has a code <i>.
    # in collect_data_by_url_list we save the tracks in dicts by length, and the dicts we save to files:
    # each dict is saved to a file under the name: "L<k>_<i>.json", where <k> represents the lengths
    # range of the tracks in the dict, cultivated in the state <i>.
    # the keys of the tracks in a dict are: "<i>_<j>". it is a string where <j> is the number of the
    # track cultivated in the state <i>.

