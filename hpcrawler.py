# TERMINOLOGY EXPLAINED:
# 1. every state has a code <i>. (sometimes referred to as index)
# 2. we save the gpx tracks in a directory named "<i>", inside of the directory GPX_DIR_PATH
# 3. we save the tracks in dicts by length, and the dicts we save to files:
#   (i) each dict is saved to a json file inside of the directory TRACKS_DIR_PATH under the name
#       "C<i>_L<l>", where <l> represents the lengths range of the tracks in the dict cultivated in the state <i>.
#   (ii) the keys of the tracks in a dict are: "C<i>_T<j>", where <j> is the number of the track cultivated
#       in the state <i>.

# TODO's:
#         2. create Enum for difficulty levels?
#         3. can we use the similarity features to decide the rank of the trail? :)
#
import sys
import gpxpy.gpx
import numpy as np
import selenium.common
from selenium import webdriver
import json
import os
import gpxpy
import pandas as pd
import SlopeMap as sm

GPX_DIR_PATH = 'hp\\gpx'
TRACKS_DIR_PATH = 'hp\\tracks'
SEEN_PATH = 'hp\\seen.json'

WAIT = 20


class HpCrawler:

    def __init__(self, to_crawl):
        """
        crawls the trails data from  "the hiking project"'s site.
        it saves the data and the progress of crawling under the "hp" directory.
        :param to_crawl: python list of countries to crawl.
                        the countries should start with a capital letter.
        """
        self._driver = None
        seen = self._load_dict(SEEN_PATH)
        self._crawl(to_crawl, seen)

    def __del__(self):
        try:
            self._driver.quit()
        except Exception as e:
            str(e)

    def _crawl(self, countries, seen):
        index = len([key for key in seen.keys() if not key.startswith('_')]) - 1

        for i in range(len(countries)):

            if countries[i] in seen:  # prevent processing the countries we've already processed
                continue

            index += 1  # new country!
            print("\n", countries[i])

            # create gpx folder for country of index i, sets up driver to website:
            self._driver = self._setup(index)

            try:
                self._driver.implicitly_wait(WAIT)
                self._log_in(self._driver)
            except selenium.common.exceptions.ElementNotInteractableException:  # race condition- driver not ready
                try:
                    self._driver.implicitly_wait(WAIT)
                    self._log_in(self._driver)
                except selenium.common.exceptions.ElementNotInteractableException:  # race condition- driver not ready
                    print('ERROR')
                    self._driver.quit()
                    return

            min_j = 0
            if ('_' + countries[i]) in seen:  # country mid-processing:
                min_j, trail_urls = seen['_' + countries[i]]
                min_j = int(min_j) + 1
            else:
                # collects all urls of country <i>'s tracks:
                trail_urls = self._trails_in_urls(self._driver, countries[i])

            print("-- collecting and processing tracks:")

            for j in np.arange(min_j, (len(trail_urls))):
                print("\t", j, "/", len(trail_urls))
                try:
                    features = self._collect_track_data(self._driver, trail_urls, index, j)
                    if features[1] >= sm.TICK:  # discards really short trails
                        len_tag, trail_dict = self._process_track_data(features, index, j)
                        HpCrawler._save_trail_data(len_tag, trail_dict)
                        print("\t\tSAVED")
                except gpxpy.gpx.GPXXMLSyntaxException as e:
                    print(str(e))
                    pass

                # update seen after every track completed:
                seen.update({'_' + countries[i]: [str(j), trail_urls]})
                self._save_dict(seen, SEEN_PATH)

            self._driver.quit()
            # update seen after every country completed:
            seen.update({countries[i]: str(index)})
            del seen['_' + countries[i]]
            self._save_dict(seen, SEEN_PATH)
            seen = self.load_seen()

    @staticmethod
    def _load_dict(path):
        """
        :param path: a json file path
        :return: dict obj, that was stored at <path>
        """
        seen = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                seen = f.read()
            seen = json.loads(seen)
        return seen

    @staticmethod
    def _save_dict(dictionary, path):
        """
        write back the dictionary <dict> to the json file at <path>
        :param dictionary: a dictionary
        :param path: a json file path
        """
        with open(path, 'w') as fp:
            json.dump(dictionary, fp)

    @staticmethod
    def load_seen():
        return HpCrawler._load_dict(SEEN_PATH)

# navigating driver #

    @staticmethod
    def _setup(index):
        """
        creates a firefox driver which is capable of downloading files without popups
        """
        print("-- setup")
        profile = webdriver.FirefoxProfile()
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)

        if not os.path.exists(GPX_DIR_PATH):
            os.makedirs(GPX_DIR_PATH)
        i_path = os.path.join(GPX_DIR_PATH, str(index))
        if not os.path.exists(i_path):
            os.makedirs(i_path)

        profile.set_preference('browser.download.dir', os.path.abspath(i_path))
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
        driver = webdriver.Firefox(firefox_profile=profile)
        driver.set_window_size(50, 1000)
        return driver

    def _log_in(self, driver):
        """
        logs into hikingproject.com
        :param driver: firefox driver
        """
        print("-- log in")
        self._homepage(driver)
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

    @staticmethod
    def _homepage(driver):
        """
        navigates the the hiking project's homepage
        :param driver: firefox driver
        """
        driver.get("https://www.hikingproject.com/")


# collects data #
    @staticmethod
    def _trails_in_urls(driver, name):
        """
        return a list of urls (strings) for paths in a country named <name>
        :param driver: firefox driver
        :param name: country's name.

        """
        print("-- collecting urls")

        HpCrawler._homepage(driver)
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
            except selenium.common.exceptions.NoSuchElementException:
                break
        trail_elements = driver.find_elements_by_xpath("//tr[@class='trail-row']")
        trail_urls = []
        for i in range(len(trail_elements)):
            trail_urls.append(trail_elements[i].get_attribute("data-href"))
        return trail_urls

    @staticmethod
    def _get_page_data(driver):
        """
        :param driver: firefox driver.
        gets data from a trail page in the hiking project: tracks length and track difficulty.
        """
        e = driver.find_elements_by_xpath("//div[@class='stat-block mx-1 pb-2']")[0]
        txt = e.text

        txt = txt.split()
        track_len = float(txt[1])
        track_dif = txt[-1]
        return track_len, track_dif

    def _collect_track_data(self, driver, urls, index, j):
        driver.get(urls[j])

        # get track's length and difficulty from site:
        track_len, track_dif = self._get_page_data(driver)

        # download gpx file:
        before = os.listdir(os.path.join(GPX_DIR_PATH, str(index)))
        driver.find_element_by_link_text("GPX File").click()
        after = os.listdir(os.path.join(GPX_DIR_PATH, str(index)))
        change = set(after) - set(before)
        filename = change.pop()  # TODO- delete dups

        return [filename, track_len, track_dif]

# processes data #
    @staticmethod
    def _save_trail_data(len_tag, trail_dict):
        if not os.path.exists(TRACKS_DIR_PATH):
            os.makedirs(TRACKS_DIR_PATH)

        dict_of_len_path = os.path.join(TRACKS_DIR_PATH, str(len_tag))
        tracks_of_len = HpCrawler._load_dict(dict_of_len_path)
        tracks_of_len.update(trail_dict)
        HpCrawler._save_dict(tracks_of_len, dict_of_len_path)

    @staticmethod
    def _process_track_data(features, index, j):

        points, track_elev = pd.DataFrame({}), pd.DataFrame({})
        filename, track_len, track_dif = features

        # open gpx file:
        gpx_file = open(os.path.join(GPX_DIR_PATH, str(index), filename), 'r', encoding="utf8")
        gpx = gpxpy.parse(gpx_file)

        # get points array & elevations:
        for track in gpx.tracks:
            for seg in track.segments:
                points = pd.DataFrame([{'lat': p.latitude, 'lon': p.longitude} for p in seg.points]) \
                    .to_numpy()
                track_elev = pd.DataFrame([{'ele': p.elevation} for p in seg.points]) \
                    .to_numpy().reshape(len(points))

        # compute slopes:
        tick = sm.get_tick(track_len)
        slopes = sm.compute_slope(points, track_elev, tick)

        # save track to the correct dict (according to the track's length):
        len_tag = sm.get_length_tag(track_len)

        return len_tag, {'C' + str(index) + '_T' + str(j): [slopes, track_dif]}