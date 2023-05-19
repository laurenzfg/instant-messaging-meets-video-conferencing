# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection()

device.touch(500, 1000, "DOWN_AND_UP")

MonkeyRunner.sleep(1)

device.touch(936, 2116, "DOWN_AND_UP")
