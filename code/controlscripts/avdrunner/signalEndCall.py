# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection()

device.touch(750, 2000, "DOWN_AND_UP")
MonkeyRunner.sleep(0.5)
device.touch(750, 2000, "DOWN_AND_UP")
