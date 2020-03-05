from enum import Enum


class PointTag(Enum):
    """
    Represents a type of an interest point on the map.
    """
    RIVER = "river"
    WATERFALL = "waterfall"
    BIRDING = "bird_hide"
    CAVE = "cave_entrance"
    WATER = "a body of water"  # Could be a lake, but also things like canals, moats etc.
    SPRING = "spring"
    GEOLOGIC = "geological"
    HISTORIC = "historic"
