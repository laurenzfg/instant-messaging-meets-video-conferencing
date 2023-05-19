# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection()

monkeylib.forceStopStartActivity(device, 'org.thoughtcrime.securesms', 'org.thoughtcrime.securesms.RoutingActivity')

MonkeyRunner.sleep(2)

# Give Focus
device.touch(0, 0, "DOWN_AND_UP")

# Initiate Call to Last Contact
device.touch(500, 400, "DOWN_AND_UP")
MonkeyRunner.sleep(1.5)

device.touch(775, 175, "DOWN_AND_UP")
MonkeyRunner.sleep(1.5)

device.touch(555, 2070, "DOWN_AND_UP")

# We should be in a call now
MonkeyRunner.sleep(3)
monkeylib.takeScreenshot(device, "/home/laurenz/aftercall.png")
