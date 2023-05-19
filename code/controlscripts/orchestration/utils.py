import math
import os
import subprocess
import time

from runner_utils import SyncProc, BGProc

from log import log


# This starts the Traffic Generator Client as a background process
def trafficgen(host, cong='cubic', receive=False, lfilename="trafficgen.log"):
    cmd = "~/mobile-vc-study-code/controlscripts/tcprunner/generator/gen -h %s -c %s %s" % (
        host, cong, "-r" if receive else "")
    return BGProc(cmd, log=True, logfile=lfilename)


# This starts the Traffic Generator Server as a background process
def trafficgenserv(lfilename="trafficgenserv.log"):
    cmd = "~/mobile-vc-study-code/controlscripts/tcprunner/generator/gen -s"
    return BGProc(cmd, log=True, logfile=lfilename)


def set_ratelimit_innerqdisc(rate: float, qdiscconfigstring: str, guid: str):
    command = "~/mobile-vc-study-code/controlscripts/router/setbandwidth_innerqdisc.sh %s \"%s\" %s" % (
        rate, qdiscconfigstring, guid)
    log(command)
    return command


def setlatency(localrtt: float, webrtt: float, guid: str):
    # localdelay is localrtt / 2 because local packets are delayed on every journy
    localrtt = (localrtt * 1.) * 0.5
    command = "~/mobile-vc-study-code/controlscripts/router/setlatency.sh %sms %sms %s" % (localrtt, webrtt, guid)
    log(command)
    return command


def count_packets(iface, filterstr, seconds=5):
    cmd = "~/mobile-vc-study-code/controlscripts/router/count_packets.sh %s %s %s" % (seconds, iface, filterstr)

    def _parser(returncode, stdout, stderr):
        d = []
        for line in stdout.split("\n"):
            if line == "":
                continue
            c, ip = line.split()
            d.append((ip, int(c)))
        return d

    return SyncProc(cmd, sudo=True, parser=_parser)


# check flow is a util for the output of count_packets
# it evalualates that for the flow (src, dst) in flows there were at least 25 pckts sent 
def check_flow(packets, source, dest):
    for srcdest, pck_count in packets:
        src, dst = srcdest.split("-")
        if src == source and dst == dest:
            if pck_count < 25:
                log("flow %s - %s less than 25 (saw %s packets) packets" % (src, dst, pck_count))
                return False
            log("flow %s - %s: %s packets" % (src, dst, pck_count))
            return True

    log("less than 25 packets (in fact NO packets)")
    return False


class tcpdump(BGProc):
    def __init__(self, iface, filename):
        self.filename = filename
        cmd = "sudo " + 'tcpdump -n -s 200 -i %s -w %s' % (iface, filename)
        super(tcpdump, self).__init__(cmd, sudo=True, log=True)

    def get_filename(self):
        return self.filename


class qmon(BGProc):
    def __init__(self, guid, qdisc):
        cmd = "sudo ~/mobile-vc-study-code/controlscripts/router/monitor.sh %s %s" % (guid, qdisc)
        super(qmon, self).__init__(cmd, sudo=True, log=True)


def make_sure_folder_exists(remoteDir):
    if not os.path.exists(remoteDir):
        os.makedirs(remoteDir)


def get_time_string():
    return time.strftime("%Y%m%d-%Hh%Mm%Ss")


def get_git_commithash():
    p = subprocess.Popen("git rev-parse HEAD".split(" "), stdout=subprocess.PIPE)
    out, err = p.communicate()
    return out


def sendmail(text):
    cmd = "echo -e \"subject: Event in Bachelor Thesis Experiment\\nfrom:from@example.net\\nto:to@example.net\\n\\n%s\\n.\" | sendmail from@example.net" % text
    p = subprocess.Popen(["bash", "-c", cmd], stdout=subprocess.PIPE)
    out, err = p.communicate()
    return out
