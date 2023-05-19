import csv
import logging
import traceback

import testbed_c_and_c
import utils
from constantins import WorkloadStep, QDiscConfig, TestConfig, qdisc_config_to_str, SCENARIO
from log import log
from runner_utils import SyncProc

dumpfolder = "/opt/grote/studydata"
exceptionCounter = 0


def _do(guid: str, functions: "list[WorkloadStep]", qdisc: QDiscConfig, bw: float, rtt: float,
        need_to_copy_screencapture=False):
    global exceptionCounter

    log("start run GUID: %s" % guid)

    qmon = utils.qmon(guid, qdisc.name)

    try:
        testbed_c_and_c.killall()
        testbed_c_and_c.enoughMem()

        # Make sure that the AVDs are configured to the correct IP
        testbed_c_and_c.issueCommandToBirds("~/mobile-vc-study-code/bootstrap/avdrunner/ifconfigavd.sh",
                                            "~/mobile-vc-study-code/bootstrap/avdrunner/ifconfigavd.sh")

        # Configure Network Environment
        qmon.start(testbed_c_and_c.btlnrunner)
        SyncProc(utils.setlatency(localrtt=rtt, webrtt=rtt,
                                  guid=guid)).start(testbed_c_and_c.btlnrunner)
        SyncProc(utils.set_ratelimit_innerqdisc(rate=bw, qdiscconfigstring=qdisc_config_to_str(qdisc),
                                                guid=guid)).start(testbed_c_and_c.btlnrunner)

        log("working on the experiment payload")
        for function in functions:
            log("starting step %s" % function.name)
            function.fun(guid)
            log("finished step %s" % function.name)

        log("stopping BPF monitor, will process the capture")
        qmon.stop()

        # Let's preprocess the raw capture
        cmd = "~/mobile-vc-study-code/controlscripts/router/process.sh " + guid
        SyncProc(cmd).start(testbed_c_and_c.btlnrunner)  # do the preprocessing

        log("capture processed, copying logs to CONTROLSERVER")
        testbed_c_and_c.btlnrunner.copyFromMeToYou(guid + "*", dumpfolder, remove=True)

        if need_to_copy_screencapture:
            log("copying screencapture to CONTROLSERVER")
            testbed_c_and_c.avda.copyFromMeToYou(guid + ".mkv", dumpfolder, remove=True)

    except Exception as e:
        logging.warning("Err in run, encountered exception")
        logging.warning(e)
        log(traceback.format_exc())

        # Alert on "too many exceptions"
        exceptionCounter = exceptionCounter + 1
        if exceptionCounter % 10 == 0:
            utils.sendmail("Encountered %d minor exceptions in run" % exceptionCounter)

    finally:
        if qmon.is_running():
            qmon.stop()

        log("end run GUID: %s" % guid)


def _bwP(c: TestConfig):
    def takeBandwidthProfile(guid):
        log("taking bw profile")
        for bw in ["3", "3", "3", "2", "1", "0.75", "0.3", "3", "3", "3", "0.3"]:
            log("setting bandwidth to %s mbit" % bw)
            SyncProc(utils.set_ratelimit_innerqdisc(rate=bw, qdiscconfigstring=qdisc_config_to_str(c.innerqdisc),
                                                    guid=guid)).start(testbed_c_and_c.btlnrunner)
            testbed_c_and_c.waitAMinute("")

    _do(c.guid,
        [WorkloadStep("make MVCA connection", testbed_c_and_c.establish_call_factory(mvca=c.mvca)),
         WorkloadStep("take bw profile", takeBandwidthProfile),
         WorkloadStep("end MVCA connection", testbed_c_and_c.end_call_factory(mvca=c.mvca))], bw=10.0,
        qdisc=c.innerqdisc,
        rtt=c.rtt)


def _incumbentTCP(c: TestConfig):
    setupTCP, killTCP = testbed_c_and_c.tcp_functions_factory(duplex=False, cong=c.cong)

    _do(c.guid,
        [WorkloadStep("Setup TCP", setupTCP),
         WorkloadStep("make MVCA connection", testbed_c_and_c.establish_call_factory(mvca=c.mvca)),
         WorkloadStep("wait", testbed_c_and_c.waitThreeMinutes),
         WorkloadStep("Kill TCP", killTCP),
         WorkloadStep("end MVCA connection", testbed_c_and_c.end_call_factory(mvca=c.mvca))], bw=c.bw,
        qdisc=c.innerqdisc,
        rtt=c.rtt)


def _incumbentCall(c: TestConfig):
    setupTCP, killTCP = testbed_c_and_c.tcp_functions_factory(duplex=False, cong=c.cong)

    _do(c.guid,
        [WorkloadStep("make MVCA connection", testbed_c_and_c.establish_call_factory(mvca=c.mvca)),
         WorkloadStep("Setup TCP", setupTCP),
         WorkloadStep("wait", testbed_c_and_c.waitThreeMinutes),
         WorkloadStep("Kill TCP", killTCP),
         WorkloadStep("end MVCA connection", testbed_c_and_c.end_call_factory(mvca=c.mvca))], bw=c.bw,
        qdisc=c.innerqdisc,
        rtt=c.rtt)


def _justCall(c: TestConfig):
    _do(c.guid,
        [WorkloadStep("make MVCA connection", testbed_c_and_c.establish_call_factory(mvca=c.mvca)),
         WorkloadStep("wait", testbed_c_and_c.waitThreeMinutes),
         WorkloadStep("end MVCA connection", testbed_c_and_c.end_call_factory(mvca=c.mvca))], bw=c.bw,
        qdisc=c.innerqdisc,
        rtt=c.rtt)


def _justCallScreencapture(c: TestConfig):
    make_screencapture = testbed_c_and_c.make_screenshot_factory()

    _do(c.guid,
        [WorkloadStep("make MVCA connection", testbed_c_and_c.establish_call_factory(mvca=c.mvca)),
         WorkloadStep("wait", testbed_c_and_c.waitThreeMinutes),
         WorkloadStep("make_screencapture", make_screencapture),
         WorkloadStep("end MVCA connection", testbed_c_and_c.end_call_factory(mvca=c.mvca))], bw=c.bw,
        qdisc=c.innerqdisc,
        rtt=c.rtt,
        need_to_copy_screencapture=True)

def _incumbentTCPScreencapture(c: TestConfig):
    setupTCP, killTCP = testbed_c_and_c.tcp_functions_factory(duplex=False, cong=c.cong)
    make_screencapture = testbed_c_and_c.make_screenshot_factory()

    _do(c.guid,
        [WorkloadStep("Setup TCP", setupTCP),
         WorkloadStep("make MVCA connection", testbed_c_and_c.establish_call_factory(mvca=c.mvca)),
         WorkloadStep("wait", testbed_c_and_c.waitThreeMinutes),
         WorkloadStep("make_screencapture", make_screencapture),
         WorkloadStep("Kill TCP", killTCP),
         WorkloadStep("end MVCA connection", testbed_c_and_c.end_call_factory(mvca=c.mvca))], bw=c.bw,
        qdisc=c.innerqdisc,
        rtt=c.rtt,
        need_to_copy_screencapture=True)


def _incumbentCallScreencapture(c: TestConfig):
    setupTCP, killTCP = testbed_c_and_c.tcp_functions_factory(duplex=False, cong=c.cong)
    make_screencapture = testbed_c_and_c.make_screenshot_factory()

    _do(c.guid,
        [WorkloadStep("make MVCA connection", testbed_c_and_c.establish_call_factory(mvca=c.mvca)),
         WorkloadStep("Setup TCP", setupTCP),
         WorkloadStep("wait", testbed_c_and_c.waitThreeMinutes),
         WorkloadStep("make_screencapture", make_screencapture),
         WorkloadStep("Kill TCP", killTCP),
         WorkloadStep("end MVCA connection", testbed_c_and_c.end_call_factory(mvca=c.mvca))], bw=c.bw,
        qdisc=c.innerqdisc,
        rtt=c.rtt,
        need_to_copy_screencapture=True)

def _justTCP(c: TestConfig):
    setupTCP, killTCP = testbed_c_and_c.tcp_functions_factory(duplex=False, cong=c.cong)

    _do(c.guid,
        [WorkloadStep("Setup TCP", setupTCP),
         WorkloadStep("wait", testbed_c_and_c.waitThreeMinutes),
         WorkloadStep("Kill TCP", killTCP)], bw=c.bw,
        qdisc=c.innerqdisc,
        rtt=c.rtt)


def evaluate_scenario(c: TestConfig):
    c = c._replace(guid=utils.get_time_string())

    metadata_header = ['guid', 'scenario', 'mvca', 'rtt', 'bw', 'innerqdisc', 'cong']
    metadata_data = [c.guid, c.scenario.name, c.mvca.name, c.rtt, c.bw, qdisc_config_to_str(c.innerqdisc), c.cong]
    with open(dumpfolder + '/' + c.guid + '.csv', 'w', encoding='UTF8') as f:
        writer = csv.writer(f)

        # write the header
        writer.writerow(metadata_header)

        # write the data
        writer.writerow(metadata_data)

    if c.scenario == SCENARIO(SCENARIO.BWP):
        _bwP(c)
    elif c.scenario == SCENARIO(SCENARIO.INCUMBENT_TCP):
        _incumbentTCP(c)
    elif c.scenario == SCENARIO(SCENARIO.INCUMBENT_CALL):
        _incumbentCall(c)
    elif c.scenario == SCENARIO(SCENARIO.JUST_CALL):
        _justCall(c)
    elif c.scenario == SCENARIO(SCENARIO.JUST_TCP):
        _justTCP(c)
    elif c.scenario == SCENARIO(SCENARIO.JUST_CALL_SCREENCAPTURE):
        _justCallScreencapture(c)
    elif c.scenario == SCENARIO(SCENARIO.INCUMBENT_TCP_SCREENCAPTURE):
        _incumbentTCPScreencapture(c)
    elif c.scenario == SCENARIO(SCENARIO.INCUMBENT_CALL_SCREENCAPTURE):
        _incumbentCallScreencapture(c)
