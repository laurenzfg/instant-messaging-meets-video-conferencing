import time

import utils
from constantins import MVCA, QDiscConfig, acceptScripts, makeScripts, endScripts, qdisc_config_to_str
from log import log
from runner_utils import SyncProc, SSHRunner, BGProc

btlnrunner = SSHRunner("x", "x")
genrunner = SSHRunner("x", "x")
genservrunner = SSHRunner("x", "x")
avda = SSHRunner("x", "x")
avdb = SSHRunner("x", "x")


# issueCommandToBirds sends the command to both bird PCs in parallel.
# avda has to finish within 8 seconds of avdb; otherwise, we rise an exception
def issueCommandToBirds(avdaCMD, avdbCMD):
    avdaProc = BGProc("`" + avdaCMD + "`")
    avdaProc.start(avda)  # in BG because this script waits for call
    log("issued command %s to avda" % avdaCMD)
    time.sleep(2)
    log("issued command %s to avdb" % avdbCMD)
    SyncProc(avdbCMD).start(avdb)
    log("avdb done")
    i = 0
    while i < 12:
        time.sleep(4)
        i = i + 4
        if avdaProc.is_running():
            log("avda still running, albeit avdb finished %ssecs ago" % i)
    assert not avdaProc.is_running()
    log("avda done")


# sends command to avda + avdb using issueCommandToBirds and asserts that
# a) we have a peer to peer udp flow between the birds
# b) the UI state of the Android phones on both birds are visually similar to a reference image
def haveTheBirdsChirp(avdaCMD, avdbCMD):
    issueCommandToBirds(avdaCMD, avdbCMD)

    log("evaluating if we have peer to peer flow")
    packets = utils.count_packets("br0", "udp", 4).start(btlnrunner)

    if not utils.check_flow(packets, "ipout", "ipin"):
        log("the birds don't chirp peer to peer")
        raise Exception()

    log("All lights green, the birds now chirp")

# enoughMem verifies that the router PC still has enough hard drive space
def enoughMem():
    ret, stdout, stderr = SyncProc("df --output=\"avail\" / | tail -1").start(btlnrunner)
    # df's output is in 1024 Byte Blocks, check if we have more than 10GBs available
    if int(stdout) * 1024 < 10 * 10 ** 9:
        log("frittezang does not have enough free memory, it only has %d" % int(stdout))
        raise Exception()

    log("frittezang does have enough free memory")

# This kills all related processes which might interfere with the measurements /
# are leftovers from a previous measurement
# This also resets the qdiscs on the bottleneck to a known good state
def killall():
    SyncProc(
        "sudo pkill -f monitorbpf.py; pkill -f tcpdump",
        sudo=True, wanted_ret=None).start(btlnrunner)
    SyncProc("pkill -f  gen", wanted_ret=[0, 1, 255]).start(genrunner)
    SyncProc("pkill -f  gen", wanted_ret=[0, 1, 255]).start(genservrunner)
    SyncProc("pkill -f monkeyrunner", sudo=True, wanted_ret=[0, 1, 255]).start(avda)
    SyncProc("pkill -f monkeyrunner", sudo=True, wanted_ret=[0, 1, 255]).start(avdb)
    SyncProc("monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/stopAllCalls.py", sudo=False).start(avda)
    SyncProc("monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/stopAllCalls.py", sudo=False).start(avdb)

    SyncProc("sudo ip tcp_metrics flush", sudo=True).start(genrunner)
    SyncProc("sudo ip tcp_metrics flush", sudo=True).start(genservrunner)
    SyncProc("sudo ip tcp_metrics flush", sudo=True).start(avda)
    SyncProc("sudo ip tcp_metrics flush", sudo=True).start(avdb)


def initialconnsettings_factory(rate=4.0, localrtt=10.0, webrtt=10.0, innerqdisc=QDiscConfig):
    qdiscconfigstr = qdisc_config_to_str(innerqdisc)

    def make_settings(guid):
        latencyCommand = utils.setlatency(localrtt=localrtt, webrtt=webrtt, guid=guid)
        rateCommand = utils.set_ratelimit_innerqdisc(rate=rate, qdiscconfigstring=qdiscconfigstr, guid=guid)

        SyncProc("%s && %s" % (latencyCommand, rateCommand)).start(btlnrunner)

    return make_settings

def make_screenshot_factory():
    def make_screenshot(guid):
        command = "mobile-vc-study-code/controlscripts/avdrunner/makeScreencapture.sh"

        SyncProc("%s %s" % (command, guid)).start(avda)

    return make_screenshot


def tcp_functions_factory(duplex, cong):
    tcpServer = utils.trafficgenserv()
    tcpClient = utils.trafficgen("btlserver", cong=cong)
    tcpClient2 = utils.trafficgen("btlserver", receive=True, cong=cong)

    def setupTCP(guid):
        log("starting tcp, duplex %s" % duplex)
        tcpServer.start(genservrunner)
        tcpClient.start(genrunner)
        if duplex:
            tcpClient2.start(genrunner)
        time.sleep(10)

    def killTCP(guid):
        assert tcpClient.is_running()
        assert tcpServer.is_running()
        if duplex:
            assert tcpClient2.is_running()

        tcpServer.stop()
        time.sleep(5)
        if tcpClient.is_running():
            # graceful shutdown failed, lol
            log("sending tcp sending failed to shut down gracefully")
            tcpClient.stop()
        if duplex and tcpClient2.is_running():
            log("receiving tcp sending failed to shut down gracefully")
            tcpClient2.stop()

    return setupTCP, killTCP

def establish_call_factory(mvca: MVCA):
    def establish_call(guid: str):
        try:
            haveTheBirdsChirp(acceptScripts[mvca], makeScripts[mvca])
        except:
            log("Retrying")
            SyncProc("pkill -f monkeyrunner", sudo=True, wanted_ret=[0, 1, 255]).start(avda)
            SyncProc("pkill -f monkeyrunner", sudo=True, wanted_ret=[0, 1, 255]).start(avdb)
            SyncProc("monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/stopAllCalls.py", sudo=False).start(
                avda)
            SyncProc("monkeyrunner ~/mobile-vc-study-code/controlscripts/avdrunner/stopAllCalls.py", sudo=False).start(
                avdb)
            time.sleep(10)
            haveTheBirdsChirp(acceptScripts[mvca], makeScripts[mvca])

    return establish_call

def end_call_factory(mvca: MVCA):
    def end_call(guid: str):
        issueCommandToBirds(endScripts[mvca], endScripts[mvca])

    return end_call


def waitAMinute(guid):
    time.sleep(60)


def waitThreeMinutes(guid):
    time.sleep(60 * 3)
