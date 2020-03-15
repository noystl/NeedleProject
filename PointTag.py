from enum import Enum


class PointTag(Enum):
    """
    Represents a type of an interest point on the map.
    """
    RIVER = "River/Creek"
    WATERFALL = "Waterfall"
    BIRDING = "Birding"
    CAVE = "Cave"
    WATER = "Lake"  # Could be a lake, but also things like canals, moats etc.
    SPRING = "Spring"
    GEOLOGIC = "Geological Significance"
    HISTORIC = "Historical Significance"
