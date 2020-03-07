import hpcrawler


def create_hp_data_set(to_crawl):
    # For The program:
    seen_countries = []
    while not set(to_crawl).issubset(set(seen_countries)):
        hpc = hpcrawler.HpCrawler(to_crawl)
        try:
            hpc.crawl()
            seen_countries = hpcrawler.HpCrawler.load_seen().keys()
        except Exception as e:
            seen = hpcrawler.HpCrawler.load_seen()
            del hpc
            print("\n", str(e), "\ninner state: ", seen, "\nstarting again..\n")
            continue

    # # For DEBUGGING:
    # hpcrawler.HpCrawler(to_crawl)
    # seen = hpcrawler.HpCrawler.load_seen()
    # print(seen)


def create_osm_data_set():
    pass


def main(to_crawl):
    # (1) PREPARE DATA:
    create_hp_data_set(to_crawl)
    create_osm_data_set()  # based on hp data set

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

    to_crawl = ['Israel']
    main(to_crawl)
