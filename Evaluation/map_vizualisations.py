"""
This module contains code for presenting some interesting stuff out model achieves on interactive maps.
"""

import folium
import math
from TrackShape import TrackShape
from OsmDataCollector import OsmDataCollector


def visualize_loop_detection(search_area):
    osm_collector = OsmDataCollector(search_area['box'])
    loop_colors = ['red', 'orange', 'darkred', 'lightred']
    not_loop_colors = ['blue', 'cadetblue', 'darkblue']

    # Calculate the center coordinate of the search area and create a map object in this area:
    location_x = (search_area['box'][1] + search_area['box'][3]) / 2
    location_y = (search_area['box'][0] + search_area['box'][2]) / 2
    output_map = folium.Map(location=[location_x, location_y], zoom_start=13)

    # Present the similar tracks on the map:
    for track in osm_collector.tracks:
        points = [(row[0], row[1]) for row in track.gps_points.values]

        if track.shape is TrackShape.LOOP:
            folium.PolyLine(points, color=loop_colors[track.id % len(loop_colors)], opacity=0.5).add_to(
                output_map)
        else:
            folium.PolyLine(points, color=not_loop_colors[track.id % len(not_loop_colors)], opacity=0.5).add_to(
                output_map)

    output_map.save('loop_detection.html')


def visualize_interest_points_recognition():
    pass


def visualize_pedestrians_recognition(search_area: dict):
    """
    Creates an interactive map where tracks who's average velocity is smaller then 5 km per hour
    are painted in blue. The rest of the tracks are painted in red.
    :param search_area: a dictionary of the form {area_name: area data} containing the data of the area we visualize.
    """
    osm_collector = OsmDataCollector(search_area['box'], speed_limit=math.inf)
    fast_colors = ['red', 'darkred', 'lightred']
    slow_colors = ['blue', 'darkblue']

    # Calculate the center coordinate of the search area and create a map object in this area:
    location_x = (search_area['box'][1] + search_area['box'][3]) / 2
    location_y = (search_area['box'][0] + search_area['box'][2]) / 2
    output_map = folium.Map(location=[location_x, location_y], zoom_start=14)

    # Present the similar tracks on the map:
    for track in osm_collector.tracks:
        points = [(row[0], row[1]) for row in track.gps_points.values]

        if track.avg_velocity <= 5:
            folium.PolyLine(points, color=slow_colors[track.id % len(slow_colors)],
                            opacity=0.5).add_to(output_map)
        else:
            folium.PolyLine(points, color=fast_colors[track.id % len(fast_colors)],
                            opacity=0.5).add_to(output_map)

    output_map.save('pedestrian_detection.html')


if __name__ == '__main__':
    areas = {'baiersbronn': {'box': [8.1584, 48.4688, 8.4797, 48.6291]},
             'louvre': {'box': [2.3295, 48.8586, 2.3422, 48.8636]}}
    # visualize_pedestrians_recognition(areas['louvre'])
    visualize_loop_detection(areas['louvre'])
