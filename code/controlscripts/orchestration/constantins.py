from enum import Enum
from typing import NamedTuple, Callable


class MVCA(Enum):
    SIGNAL = 1,
    WHATSAPP = 2,
    TELEGRAM = 3,


acceptScripts = {
    MVCA.SIGNAL: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/signalAcceptCall.py",
    MVCA.WHATSAPP: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/whatsappAcceptCall.py",
    MVCA.TELEGRAM: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/telegramAcceptCall.py"
}

makeScripts = {
    MVCA.SIGNAL: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/signalMakeCall.py",
    MVCA.WHATSAPP: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/whatsappMakeCall.py",
    MVCA.TELEGRAM: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/telegramMakeCall.py"
}

endScripts = {
    MVCA.SIGNAL: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/signalEndCall.py",
    MVCA.WHATSAPP: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/whatsappEndCall.py",
    MVCA.TELEGRAM: "monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/telegramEndCall.py"
}


class WorkloadStep(NamedTuple):
    name: str
    fun: Callable[[str], None]


class QDiscConfig(NamedTuple):
    name: str
    len: int


def qdisc_config_to_str(config: QDiscConfig) -> str:
    qdiscconfigstr = config.name
    if qdiscconfigstr == "bfifo":
        qdiscconfigstr = qdiscconfigstr + " limit " + str(config.len)

    return qdiscconfigstr


CODEL = QDiscConfig("codel", -1)
FQCODEL = QDiscConfig("fq_codel", -1)


class SCENARIO(Enum):
    BWP = 101,
    INCUMBENT_CALL = 102,
    INCUMBENT_TCP = 103,
    JUST_TCP = 104,
    JUST_CALL = 105,
    JUST_CALL_SCREENCAPTURE = 106,
    INCUMBENT_CALL_SCREENCAPTURE = 201,
    INCUMBENT_TCP_SCREENCAPTURE = 202,


class TestConfig(NamedTuple):
    guid: str
    scenario: SCENARIO
    mvca: MVCA
    rtt: float
    bw: float
    innerqdisc: QDiscConfig
    cong: str
