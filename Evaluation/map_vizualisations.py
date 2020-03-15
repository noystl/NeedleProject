"""
This module contains code for presenting some interesting stuff out model achieves on interactive maps.
"""
import os
import folium
import math

from geopy.distance import geodesic

from Evaluation.eval_interest_points import get_candidates
from PointTag import PointTag
from TrackShape import TrackShape
from OsmDataCollector import OsmDataCollector


def visualize_loop_detection(search_area):
    osm_collector = OsmDataCollector(search_area['box'], speed_limit=math.inf)
    loop_colors = ['red', 'orange', 'darkred', 'lightred']
    not_loop_colors = ['blue', 'purple']
    # Calculate the center coordinate of the search area and create a map object in this area:
    location_x = (search_area['box'][1] + search_area['box'][3]) / 2
    location_y = (search_area['box'][0] + search_area['box'][2]) / 2
    output_map = folium.Map(location=[location_x, location_y], zoom_start=13)

    # Present the similar tracks on the map:
    for track in osm_collector.tracks:
        points = [(row[0], row[1]) for row in track.gps_points.values]

        if track.deduce_track_shape(thresh=100) is TrackShape.LOOP:
            folium.PolyLine(points, color=loop_colors[track.id % len(loop_colors)], opacity=0.5).add_to(
                output_map)
        else:
            folium.PolyLine(points, color=not_loop_colors[track.id % len(not_loop_colors)], opacity=0.5).add_to(
                output_map)

    output_map.save('loop_detection.html')


def visualize_interest_points_recognition(search_area: dict, tag: PointTag):
    """
    Creates an interactive map of the search_area, that presents interest point of PointTag tag
    (an water drop pin) and tracks (trail and a information pin holding the track's index).
    The interest points that are close to at least one track in search_area are painted in black,
    and hold the indices of the tracks they are close to.
    The other interest points are painted gray. the tracks are painted in other colors.
    The map is saved under 'visualizations\\<tag>\\interest_points_vis.html'
    :param search_area: a dictionary of the form {area_name: area data} containing the data of
    :param tag : PointTag
    the area we want to visualize.
    """
    area_path = os.path.join('InterestPointsData', tag.value)
    osm_collector = OsmDataCollector(search_area['box'], speed_limit=math.inf)
    tracks = osm_collector.tracks
    candidates = get_candidates(area_path, tag, tracks)
    location_x = (search_area['box'][1] + search_area['box'][3]) / 2
    location_y = (search_area['box'][0] + search_area['box'][2]) / 2
    output_map = folium.Map(location=[location_x, location_y], zoom_start=13)
    colors = ['cadetblue', 'darkpurple', 'purple', 'green', 'darkgreen', 'darkred', 'lightred', 'red',
              'orange', 'blue', 'lightblue', 'darkblue', 'pink', 'lightgray', 'lightgreen']

    markers = {}
    for track_idx, track in enumerate(tracks):
        track_color = colors[track.id % len(colors)]

        # Present track on map, and pin it by idx:
        folium.PolyLine(track.gps_points.to_numpy()[:, :2], color=track_color, opacity=1).add_to(output_map)
        folium.Marker(
            location=[track.gps_points.to_numpy()[:, :2][-1][0], track.gps_points.to_numpy()[:, :2][-1][1]],
            popup='track ' + str(track_idx),
            icon=folium.Icon(color=track_color, icon='info-sign')
        ).add_to(output_map)

        # checks the proximity of a track to it's candidates, saves results under marks:
        if not candidates[track_idx].empty:
            lats, lons = candidates[track_idx]['lat'], candidates[track_idx]['lon']

            for idx, point in candidates[track_idx].iterrows():

                if track.is_close(point, samp_ratio=1, closeness_thresh=200):
                    if (lats[idx], lons[idx]) in markers:
                        markers[(lats[idx], lons[idx])] += ("\n" + str(track_idx))
                    else:
                        markers[(lats[idx], lons[idx])] = "tracks: " + str(track_idx)
                else:
                    if not (lats[idx], lons[idx]) in markers:
                        markers[(lats[idx], lons[idx])] = ""

    # Present the candidates on map:
    for key in markers.keys():
        if markers[key]:
            folium.Marker(location=key, popup=markers[key], icon=folium.Icon(color='black', icon='plus'))\
                .add_to(output_map)
        else:
            folium.Marker(location=key, icon=folium.Icon(color='black', icon='minus')).add_to(output_map)

    output_map.save('interest_points_vis.html')


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
             'louvre': {'box': [2.3295, 48.8586, 2.3422, 48.8636]},
             'disingof': {'box': [34.7782, 32.0822, 34.7970, 32.0920]},
             'arc_de_triomphe': {'box': [4.80318, 44.1414, 4.8062, 44.14302]},
             'stone': {'box': [-1.83028, 51.17762, -1.82311, 51.18148]},
             'germany': {'box': [10.2868, 51.7070, 10.6780, 51.9065]},
             }
    visualize_interest_points_recognition(areas['germany'], PointTag.WATERFALL)
    visualize_pedestrians_recognition(areas['louvre'])
    visualize_loop_detection(areas['stone'])
