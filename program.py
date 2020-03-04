
import hpcrawler


def main():

    # countries crawled so far - Australia, Brazil, France, Italy, Switzerland, South Africa, United Kingdom
    # ,'Alaska', 'Alabama', 'Illinois', 'Florida', 'Ohio', 'Rhode Island', 'Vermont']

    to_crawl = ['Australia', 'Brazil', 'France', 'Italy', 'Switzerland', 'South Africa', 'United Kingdom',
                'Alaska', 'Alabama', 'Illinois', 'Florida', 'Ohio', 'Rhode Island', 'Vermont']

    # (1) PREPARE DATA:

    # get hp data-
    hpcrawler.HpCrawler(to_crawl)
    # get osm data (completed from hp data)-

    # (2) SUPPORT USER QUERIES:

    stay = 1
    while stay:

    # get query-

    # get response to query-

    # present response to user-

    # end-

        stay = 0

