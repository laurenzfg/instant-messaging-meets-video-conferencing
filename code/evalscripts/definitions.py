from typing import Dict, List, NamedTuple
import pandas

class TimelineElement(NamedTuple):
    timestamp: pandas.DatetimeIndex
    event: str
    payload: str

class Specfile(NamedTuple):
    GUID: str
    frontmatter: Dict[str, str]
    timeline: List