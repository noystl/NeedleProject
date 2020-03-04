import hpcrawler


def main(to_crawl):
    # (1) PREPARE DATA:

    # get hp data-
    hpc = hpcrawler.HpCrawler(to_crawl)
    print(hpc.load_seen())

    # get osm data (completed from hp data)-

    # (2) SUPPORT USER QUERIES:

    stay = 1
    while stay:

    # get query-

    # get response to query-

    # present response to user-

    # end-

        stay = 0


if __name__ == '__main__':
    # countries crawled so far - Australia, Brazil, France, Italy, Switzerland, South Africa, United Kingdom
    # ,'Alaska', 'Alabama', 'Illinois', 'Florida', 'Ohio', 'Rhode Island', 'Vermont']

    # to_crawl = ['Australia', 'Brazil', 'France', 'Italy', 'Switzerland', 'South Africa', 'United Kingdom',
    #

    to_crawl = ['Australia', 'Brazil', 'France']
    main(to_crawl)
