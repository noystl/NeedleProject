import gpxpy.gpx
import numpy as np
import selenium.common
from selenium import webdriver
import json
import os
import gpxpy
import pandas as pd
import slopeMap as sm
import re
from PointTag import PointTag


class HpCrawler:
    """
    This class crawls "The Hiking Project"'s website: https://www.hikingproject.com/.
    It process the data crawled, and saves it, as follows:
    it creates a dir named "hp", that contains 2 dirs and a file:
     (1) dir <gpx_dir_path> : contains country directories, each directory holds all gpx files of the tracks
                            crawled from that country and a json file keeping trace of the data collecting progress
                            * The dir is named by the country name, string: <country>
                            * The gpx files are named by the track's idx, int >= 0: <j>
                            * The json file is named <progress>: maps [track_gpx_filename,track_difficulty]
                                to track idx <j>, int >=0.
     (2) dir <tracks_dir_path> : contains json files. These files are named by the length_tag of the tracks
                                they hold: int >= 0 denoted as <l>.
                                each json files holds a dict mapping the track name: <country><j>
                                to the track's representation.
     (3) json file <seen_path> : Keeps trace of the mining progress: contains a dict that maps the progress
                                to the country <country>:
                                [idx_of_next_track_we_need_to_crawl, [<urls>]] if we're mid process,
                                and 'Done' otherwise.
    """

    # static fields:
    wait = 5
    done_tag = 'DONE'
    gpx_dir_path = 'hp\\gpx'
    tracks_dir_path = 'hp\\tracks'
    seen_path = 'hp\\seen.json'

    def __init__(self, to_crawl, gpx_dir='hp\\gpx', tracks_dir='hp\\tracks', seen='hp\\seen.json'):
        """
        crawls the trails data from "the hiking project"'s site.
        it saves the data and the progress of crawling task under the "hp" directory.
        :param to_crawl: python list of countries to crawl.
                        the countries should start with a capital letter.
        """
        HpCrawler.gpx_dir_path = gpx_dir
        HpCrawler.tracks_dir_path = tracks_dir
        HpCrawler.seen_path = seen
        self._countries = to_crawl
        self._country = None  # string
        self._track_idx = str(0)  # always string
        self._path = None  # the location of collected data: gpx and progress of collecting (not final data)
        self._url = None  # python list of strings
        self._driver = None  # firefox(!) driver
        self._driver_status = False

    def __del__(self):
        """
        closes the driver in case an exception that hasn't been treated has occurred
        """
        if self._driver_status is True:
            self._driver.quit()

# writing to, and reading from, dicts in json files #
    @staticmethod
    def _load_dict(path):
        """
        :param path: a json file path
        :return: dict obj, that was stored at <path>
        """
        dictionary = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                file = f.read()
            dictionary = json.loads(file)
        return dictionary

    @staticmethod
    def _save_dict(dictionary, path):
        """
        write back the dictionary <dict> to the json file at <path>
        :param dictionary: a dictionary
        :param path: a json file path
        """
        with open(path, 'w') as f:
            json.dump(dictionary, f, indent=4)

    @staticmethod
    def load_seen():
        return HpCrawler._load_dict(HpCrawler.seen_path)

    @staticmethod
    def _save_track_data(len_tag, track_dict):
        """
        saves the track_dict to the json file named <len_tag> under <HpCrawler.tracks_dir_path>
        :param len_tag: the track's length tag: see SlopeMap
        :param track_dict: the track's representation:
        """
        if not os.path.exists(HpCrawler.tracks_dir_path):
            os.makedirs(HpCrawler.tracks_dir_path)

        dict_of_len_path = os.path.join(HpCrawler.tracks_dir_path, str(len_tag) + ".json")
        tracks_of_len = HpCrawler._load_dict(dict_of_len_path)
        tracks_of_len.update(track_dict)
        HpCrawler._save_dict(tracks_of_len, dict_of_len_path)

    @staticmethod
    def check_list(features):
        new_features = []
        if 'River/Creek' in features:
            new_features.append(PointTag.RIVER.value)
        if 'Waterfall' in features:
            new_features.append(PointTag.WATERFALL.value)
        if 'Birding' in features:
            new_features.append(PointTag.BIRDING.value)
        if 'Cave' in features:
            new_features.append(PointTag.CAVE.value)
        if 'Lake' in features:
            new_features.append(PointTag.WATER.value)
        elif 'Fishing' in features:
            new_features.append(PointTag.WATER.value)
        elif 'Swimming' in features:
            new_features.append(PointTag.WATER.value)
        if 'Geological Significance' in features:
            new_features.append(PointTag.GEOLOGIC.value)
        if 'Historical Significance' in features:
            new_features.append(PointTag.HISTORIC.value)
        return new_features

    # driver setup and web navigating #
    def _setup(self):
        """
        creates a firefox driver which is capable of downloading files without popups
        """
        print("-- setup")
        profile = webdriver.FirefoxProfile()
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)

        profile.set_preference('browser.download.dir', os.path.abspath(self._path))
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
        driver = webdriver.Firefox(firefox_profile=profile)
        driver.set_window_size(50, 1000)
        self._driver_status = True
        return driver

    def _log_in(self):
        """
        logs into "the Hiking Project"'s website
        """
        print("-- log in")
        self._homepage()
        elem = self._driver.find_element_by_link_text("Sign In")
        elem.click()
        elem_email = self._driver.find_element_by_xpath("//input[@placeholder='Log in with email']")
        elem_email.clear()
        elem_email.send_keys("matan.pinkas@mail.huji.ac.il")
        elem_pw = self._driver.find_element_by_xpath("//input[@placeholder='Password']")
        elem_pw.clear()
        elem_pw.send_keys("313287237mM")
        elem = self._driver.find_elements_by_xpath("//button[@class='btn btn-primary btn-lg']")
        for e in elem:
            if e.text == "Log In":
                elem = e
        elem.click()

    def _homepage(self):
        """
        navigates to "the hiking project"'s homepage
        """
        self._driver.get("https://www.hikingproject.com/")

# collects data #

    def _trails_in_urls(self):
        """
        return a list of urls (strings) for tracks in the current country
        """
        print("-- collecting urls")

        self._homepage()
        query = "//a[@title='" + self._country + "']"
        elem = self._driver.find_element_by_xpath(query)
        url = elem.get_attribute("href")
        self._driver.get(url)
        # driver is not at page with data on paths in <name>
        # loop makes page show all trails in <name>

        while True:
            try:
                show_more = self._driver.find_element_by_xpath("//button[@id='load-more-trails']")
                show_more.click()
            except selenium.common.exceptions.NoSuchElementException:
                break
        trail_elements = self._driver.find_elements_by_xpath("//tr[@class='trail-row']")
        trail_urls = []
        for i in range(len(trail_elements)):
            trail_urls.append(trail_elements[i].get_attribute("data-href"))
        return trail_urls

    def _get_page_data(self):
        """
        gets data from a trail page in the hiking project: track's difficulty, track length and features.
        :returns: track_dif: string representation of enum of class TrackDifficulty
                  track_length: string representation of track length in km
                  features: a list of strings of features
        """
        e = self._driver.find_elements_by_xpath("//div[@class='stat-block mx-1 pb-2']")[0]
        txt = e.text
        txt = txt.split()
        track_length = txt[1]
        track_shape = txt[3:]
        track_shape = track_shape[:-1]
        if track_shape[-1] == 'Very':  # if track difficulty is very difficult need to correct
            track_shape = track_shape[:-1]
            track_dif = txt[-2] + " " + txt[-1]
        else:
            track_dif = txt[-1]
        shp = ""
        for w in track_shape:
            shp += w + " "
        shp = shp[:-1]
        try:
            features_element = self._driver.find_element_by_xpath("//span[@class='font-body pl-half']")
            features = features_element.text.split(" · ")
        except:  # basically should only fail when a page doesnt have features
            features = []
        features = HpCrawler.check_list(features)
        return track_dif, track_length, shp, features

    def _collect_track_data(self):
        """
        collects and saves the track's data: difficulty, the gpx file, and it's filename.
        :return: the track's features: [filename, track_dif, track length, track shape, [features]]
        """

        progress = HpCrawler._load_dict(os.path.join(self._path, "progress.json"))
        if self._track_idx in progress:  # data was collected previously
            return progress[self._track_idx]

        j_gpx_path = os.path.join(self._path, self._track_idx)
        self._driver.get(self._url)

        # get track's difficulty from site:
        track_dif, track_length, track_shape, features = self._get_page_data()

        # download gpx file (if needed) and get the download's name:
        if not os.path.exists(j_gpx_path + ".gpx"):  # if gpx file hasn't been downloaded before
            before = os.listdir(self._path)
            self._driver.find_element_by_link_text("GPX File").click()
            after = os.listdir(self._path)
            change = set(after) - set(before)
            filename = change.pop()
            dup_file = re.findall(r'.*\(\d+\)\.gpx', filename)

            # handles the case we've just saved dup file, due to connection problems at last connection:
            # NOTE: does NOT handle the case of multiple dup files saved due to reoccurring connection problems
            # at the exact same spot (although it's not likely to happen).
            # it deletes only the file we've saved in this current connection.
            if dup_file:
                os.remove(os.path.join(self._path, filename))  # delete duplicate
                filename = re.sub(r'\(\d+\)\.gpx', '', filename) + ".gpx"  # work with the original one
            os.rename(os.path.join(self._path, filename), j_gpx_path + ".gpx")

        else:
            filename = progress[self._track_idx][0]

        # update and save the progress, what we've mined so far:
        # NOTE:
        # (1) we want to save filename for future use: when re-mining a country that
        # was mined before, we'll be able to see which tracks we've processed before.
        # (2) we rather save the gpx files by their <j> because it's unique and it allows
        # us to keep mining from where we've stopped (ints are ordered).
        progress.update({self._track_idx: [filename, track_dif, track_length, track_shape, features]})
        self._save_dict(progress, os.path.join(self._path, "progress.json"))

        return [filename, track_dif]

# processes data #

    def _process_track_data(self, features):
        """
        process the track's data that was collected.
        :param features:  the track's features: [filename, track_dif]
        :return: the track's len_tag: see SlopeMap
                the track's representation:  dict {<country>_<j>: [points, elevation, length, track_dif]}
                if the track is to short for processing- returns None
        """

        points, track_elev = pd.DataFrame({}), pd.DataFrame({})
        filename, track_dif = features

        # open gpx file:
        gpx_file = open(os.path.join(HpCrawler.gpx_dir_path, self._country, self._track_idx + ".gpx"),
                        'r', encoding="utf8")
        gpx = gpxpy.parse(gpx_file)

        # get points array & elevations:
        for track in gpx.tracks:
            for seg in track.segments:
                points = pd.DataFrame([{'lat': p.latitude, 'lon': p.longitude} for p in seg.points]) \
                    .to_numpy()
                track_elev = pd.DataFrame([{'ele': p.elevation} for p in seg.points]) \
                    .to_numpy().reshape(len(points))

        track_len = sm.compute_track_km(points)[-1]
        if track_len < sm.TICK:  # discards too short of a track
            return None

        # computes the track's len_tag for future use:
        len_tag = sm.get_length_tag(track_len)

        return len_tag, \
               {self._country + '_' + self._track_idx: [points.tolist(), track_elev.tolist(), track_len, track_dif]}

# runs functionality:

    def crawl(self):
        """
        crawls the trails data from "the hiking project"'s site.
        it saves the data and the progress of crawling under the "hp" directory.
        :return all of the countries we've crawled so far (not just in this iteration)
        """
        for i in range(len(self._countries)):
            seen = HpCrawler.load_seen()
            self._country = self._countries[i]

            if self._country in seen and seen[self._country] == HpCrawler.done_tag:  # country done processing
                continue

            print("\n", self._country)

            # create gpx folder for country of index i, sets up driver to website:
            self._path = os.path.join(HpCrawler.gpx_dir_path, self._country)
            if not os.path.exists(self._path):
                os.makedirs(self._path)

            self._driver = self._setup()
            while True:
                try:
                    self._driver.implicitly_wait(HpCrawler.wait)
                    self._log_in()
                    break
                except selenium.common.exceptions.ElementNotInteractableException:  # race condition- driver not ready
                    print("USAGE: Do not minimize the window until logged in.")

            if self._country in seen:  # country mid-processing:
                self._track_idx, trail_urls = seen[self._country]
            else:  # new country!
                trail_urls = self._trails_in_urls()
                seen.update({self._country: [self._track_idx, trail_urls]})
                HpCrawler._save_dict(seen, HpCrawler.seen_path)

            # start mining:
            print("-- collecting and processing")

            start_id = int(self._track_idx)
            for j in np.arange(start_id, (len(trail_urls) + start_id)):

                # trails we didn't finish processing
                print("\t", j - start_id, "/", len(trail_urls))
                self._track_idx = str(j)
                self._url = trail_urls[j - start_id]
                features = self._collect_track_data()

                try:
                    self._track_idx = str(j)
                    track_data = self._process_track_data(features)
                except gpxpy.gpx.GPXXMLSyntaxException as e:
                    print(str(e))
                    continue

                # discards short trails (but collect it's data for optional future use):
                if track_data is not None:  # the track is long enough
                    HpCrawler._save_track_data(track_data[0], track_data[1])

                # update seen after every track processing is completed:
                seen.update({self._country: [str(int(self._track_idx) + 1), trail_urls]})
                HpCrawler._save_dict(seen, HpCrawler.seen_path)

            self._driver.quit()
            self._driver_status = False

            # update seen after every country completed:
            seen.update({self._country: HpCrawler.done_tag})
            HpCrawler._save_dict(seen, HpCrawler.seen_path)


if __name__ == "__main__":

    to_crawl = ['Spain', 'France', 'Nevada']
    crawler = HpCrawler(to_crawl)
    crawler.crawl()
