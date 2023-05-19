# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
print("wait for conn")
device = MonkeyRunner.waitForConnection()
print("got conn")

monkeylib.stopAllMessengers(device)
