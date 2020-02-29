import pandas as pd


def generate_test_tracks(n=10) -> list:
    """
    Generates n tracks (pandas data frames of the form (lat, lon)) for the slopes POC.
    :param n: the number of tracks to generate.
    :return: a list of the generated tracks.
    """
    t1 = pd.DataFrame([{'lat': 1, 'lon': 1}, {'lat': 2, 'lon': 2}])  # Nonsense. To remove and implement the real func.
    t2 = pd.DataFrame([{'lat': 2, 'lon': 2}, {'lat': 1, 'lon': 2}])
    t3 = pd.DataFrame([{'lat': 1, 'lon': 1}, {'lat': 4, 'lon': 1}])
    dummy_test_tracks = [t1, t2, t3]
    return dummy_test_tracks


def generate_osm_track() -> pd.DataFrame:
    """
    Generates a pandas data frame (lat, lon) of an osm track. In the experiment, we'll try to
    find the closest track to this one.
    :return: pandas df as described above.
    """
    dummy_points = \
        pd.DataFrame([{'lat': 1, 'lon': 1}, {'lat': 2, 'lon': 2}])  # Nonsense. To remove and implement this shit.
    return dummy_points

# The code in the branch osm_data_collector might be useful. We can thing of a smart way to reuse it, or if we are
# short in time, to copy&paste.
