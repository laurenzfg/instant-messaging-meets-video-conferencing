#!/usr/bin/env python3
from math import ceil

import utils

import scenarios
from log import log
import constantins
from constantins import MVCA, QDiscConfig
import logging
import sys
import traceback

run_guid = utils.get_time_string()

# Config Logging
log_format = '[%(asctime)-15s] %(message)s'
commit = utils.get_git_commithash()
log_formatter = logging.Formatter(log_format)
logging.basicConfig(level=logging.INFO, filename="/opt/grote/thesislogs/%s.log" % run_guid, format=log_format)
log_stream_handler = logging.StreamHandler()
log_stream_handler.setFormatter(log_formatter)
logging.getLogger().addHandler(log_stream_handler)


def _exception_hook(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(
        exc_type, exc_value, exc_traceback))


sys.excepthook = _exception_hook

log("git commit: %s " % commit)
log("run guid: %s " % run_guid)

# Here we invoke the actual test scenarios
try:
    iters = 30
    mvcas = MVCA.TELEGRAM, MVCA.SIGNAL, MVCA.WHATSAPP
    for i in range(iters):
        log("running iter %s out of %s" % (i, iters))
        for rtt in [50]:
            # for mvca in mvcas:
            #     innerqdisc = QDiscConfig("bfifo", 10000)
            #
            #     bwPScenarioConfig = constantins.TestConfig("<invalidguid>", constantins.SCENARIO.BWP, mvca, rtt, -1.0,
            #                                                innerqdisc, "<nocong>")
            #     scenarios.evaluate_scenario(bwPScenarioConfig)

            for bw in [0.3, 2.0]:
                bdp = float(rtt * bw * 10.0 ** 3) / 8.0
                
                for cong in ["bbr2", "bbr", "cubic"]:  # reintroduce "reno"
                    for scenario in [constantins.SCENARIO.INCUMBENT_TCP, constantins.SCENARIO.INCUMBENT_CALL]:
                        for buffscalar in [10.0, 1.0]:
                            for mvca in mvcas:
                                bufferlen = int(ceil(buffscalar * bdp))
                                innerqdisc = QDiscConfig("bfifo", bufferlen)

                                scenarios.evaluate_scenario(
                                    constantins.TestConfig("<invalidguid>", scenario, mvca, rtt, bw,
                                                           innerqdisc, cong))

except KeyboardInterrupt as e:
    log(traceback.format_exc())
    pass
except Exception as e:
    # Uncatched Exceptions are reported via E-Mail, exception in test runs are just logged
    log(traceback.format_exc())
    utils.sendmail("Aborted %s due to exception" % run_guid)

utils.sendmail("Bachelor Experiment Exited")
