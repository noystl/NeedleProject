# TERMINOLOGY EXPLAINED:
# 1. every state has a code <i>. (sometimes referred to as index)
# 2. we save the gpx tracks in a directory named "<i>", inside of the directory GPX_DIR_PATH
# 3. we save the tracks in dicts by length, and the dicts we save to files:
#   (i) each dict is saved to a json file inside of the directory TRACKS_DIR_PATH under the name
#       "C<i>_L<l>", where <l> represents the lengths range of the tracks in the dict cultivated in the state <i>.
#   (ii) the keys of the tracks in a dict are: "C<i>_T<j>", where <j> is the number of the track cultivated
#       in the state <i>.

# TODO's: 1. don't delete and re-download gpx files of a country if we didn't finished,
#            although the program can crash and we'll lose the site's features?
#         2. create Enum for difficulty levels?
#         3. can we use the similarity features to decide the rank of the trail? :)
#         4. doesn't know 'AUSTRALIA', 'daef#' -  what to do?

import shutil
from selenium import webdriver
import json
import os
import gpxpy
import pandas as pd
import SlopeMap as sm

GPX_DIR_PATH = 'hp\\hp_gpx'
TRACKS_DIR_PATH = 'hp\\hp_tracks'


class HpCrawler:

    def __init__(self, to_crawl):
        # read back the dict holding the countries we've already processed:
        prev_seen = {}
        if os.path.exists("hp\\seen.json"):
            with open("hp\\seen.json", "r") as f:
                prev_seen = f.read()
            prev_seen = json.loads(prev_seen)

        this_pass = self._runs(to_crawl, prev_seen)

        # write back the dictionary now containing the previously processed countries
        # and the countries we've processed in this pass:
        prev_seen.update(this_pass)
        seen = json.dumps(prev_seen)
        f = open("hp\\seen.json", "w")
        f.write(seen)
        f.close()

    def _setup(self, index):
        """
        creates a firefox driver which is capable of downloading files without popups
        """
        print("setup")
        profile = webdriver.FirefoxProfile()
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)

        if not os.path.exists(GPX_DIR_PATH):
            os.makedirs(GPX_DIR_PATH)
        i_path = os.path.join(GPX_DIR_PATH, str(index))
        if os.path.exists(i_path):
            shutil.rmtree(i_path, ignore_errors=True)
        os.makedirs(i_path)

        profile.set_preference('browser.download.dir', os.path.abspath(i_path))
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
        driver = webdriver.Firefox(firefox_profile=profile)
        return driver

    def _log_in(self, driver):
        """
        logs into hikingproject.com
        :param driver: firefox driver
        """
        print("log in")
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
        return

    def _homepage(self, driver):
        """
        navugates the the hiking project's homepage
        :param driver: firefox driver
        """
        driver.get("https://www.hikingproject.com/")

    def _trails_in_urls(self, driver, name):
        """
        return a list of urls (strings) for paths in a country named <name>
        :param driver: firefox driver
        :param name: country's name.

        """
        self._homepage(driver)
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

    def _get_download_file_name(self, before, path):
        after = os.listdir(path)
        change = set(after) - set(before)
        if len(change) == 1:
            return change.pop()

    def _get_page_data(self, driver):
        """
        gets data from a trail page in the hiking project: tracks length and track difficulty.
        """
        e = driver.find_elements_by_xpath("//div[@class='stat-block mx-1 pb-2']")[0]
        txt = e.text
        txt = txt.split()
        track_len = float(txt[1])
        track_dif = txt[-1]
        return track_len, track_dif

    def _save_data(self, data, index):
        """
        saves t
        he data's inner dicts to a json file inside of the directory TRACKS_DIR_PATH under the name
        "<i>_<l>", where <l> represents the lengths range of the tracks in the dict cultivated in the state <i>.
        :param data: python list of dicts, each dict holds tracks of length tag  <k>.
        :param index: country idx
        """
        if not os.path.exists(TRACKS_DIR_PATH):
            os.makedirs(TRACKS_DIR_PATH)

        num_of_dicts = sm.get_num_of_len_tags()
        for l in range(num_of_dicts):
            if data[l]:  # if the dict isn't empty (... we'll save it)
                path = os.path.join(TRACKS_DIR_PATH, 'C' + str(index) + '_L' + str(l) + '.json')
                with open(path, 'w') as f:
                    json.dump(data[l], f)

    def _collect_tracks_data(self, driver, urls, index):
        """
        downloads gpx of given trails
        :param driver: selenium webdriver
        :param urls: list of urls of web pages in hikingproject.com
        :param index: number of state
        """
        features = {}
        print("urls: ", len(urls))

        # for j in range(1):  # TODO - for testing
        for j in range(len(urls)):
            driver.get(urls[j])

            # get track's length and difficulty from site:
            track_len, track_dif = self._get_page_data(driver)

            # download gpx file:
            before = os.listdir(os.path.join(GPX_DIR_PATH, str(index)))
            driver.find_element_by_link_text("GPX File").click()
            after = os.listdir(os.path.join(GPX_DIR_PATH, str(index)))
            change = set(after) - set(before)
            filename = change.pop()

            features[j] = [filename, track_len, track_dif]

            print("f", j, ": ", filename)
        return features

    def _process_tracks_data(self, features, index):
        num_of_dicts = sm.get_num_of_len_tags()
        data = [dict() for x in range(num_of_dicts)]
        points, track_elev = pd.DataFrame({}), pd.DataFrame({})

        for j in range(len(features)):
            filename, track_len, track_dif = features[j]

            # open gpx file:
            gpx_file = open(os.path.join(GPX_DIR_PATH, str(index), filename), 'r', encoding="utf8")
            gpx = gpxpy.parse(gpx_file)

            # get points array & elevations:
            for track in gpx.tracks:
                for seg in track.segments:
                    points = pd.DataFrame([{'lat': p.latitude, 'lon': p.longitude} for p in seg.points]).to_numpy()
                    track_elev = pd.DataFrame([{'ele': p.elevation} for p in seg.points])\
                        .to_numpy().reshape(len(points))

            # compute slopes:
            tick = sm.get_tick(track_len)
            slopes = sm.compute_slope(points, track_elev, tick)

            # save track to the correct dict (according to the track's length):
            len_tag = sm.get_length_tag(track_len)

            data[len_tag]['C' + str(index) + '_T' + str(j)] = [slopes, track_dif]
        self._save_data(data, index)

    def _runs(self, countries, seen):
        """
        runs the hp data crawling and data processing, for the countries supplied in <countries>,
        excluding the ones that appear in <seen>.
        :param countries: python list of countries whom trails we want to download
        :param seen: a dictionary of the countries we've already processed (to prevent double crawling)
        :return: a dictionary of the new countries from <countries> (that are not in <seen>),
                we've processed ib this pass. the keys are strings (country name as given in <countries>),
                the values are the country id (int).
        """
        index = len(seen.keys()) - 1
        this_pass = {}

        for i in range(len(countries)):

            if countries[i] in seen:  # prevent processing the countries we've already processed
                continue

            index += 1  # new country!
            print("\n", countries[i])

            # create gpx folder for country of index i, sets up driver to website:
            ff_driver = self._setup(index)
            try:  # TODO: catch-> try again
                self._log_in(ff_driver)
            except:
                self._log_in(ff_driver)

            # collects all urls of country <i>'s tracks:
            trail_urls = self._trails_in_urls(ff_driver, countries[i])

            # collects the data from web, and downloads the gpx files:
            fs = self._collect_tracks_data(ff_driver, trail_urls, index)

            # process the data from web and from the gpx to create a representation of
            # our liking and saves it under a folder it creates for country <i>:
            self._process_tracks_data(fs, index)

            this_pass[countries[i]] = index
        return this_pass
