from enum import Enum


class PointTag(Enum):
    """
    Represents a type of an interest point on the map.
    """
    WATER = "River"
    HISTORIC = "Historic"
