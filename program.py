import hpcrawler


def main(to_crawl):
    # (1) PREPARE DATA:

    # get hp data-
    seen = {}
    while seen.keys() != set(to_crawl):
        try:
            hpcrawler.HpCrawler(to_crawl)
        except Exception as e:
            print("\n", str(e), "\nstarting again..\n")
            seen = hpcrawler.HpCrawler.load_seen()
            print(seen)
            continue

    # hpcrawler.HpCrawler(to_crawl)
    # seen = hpcrawler.HpCrawler.load_seen()
    # print(seen)

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

    to_crawl = ['Brazil', 'Australia', 'France', 'Italy', 'Switzerland']
    main(to_crawl)
