# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection()

monkeylib.forceStopStartActivity(device, 'org.thoughtcrime.securesms', 'org.thoughtcrime.securesms.RoutingActivity')

# Give Focus
device.touch(0, 0, "DOWN_AND_UP")

monkeylib.pressButtonAsSoonAsItIsOnScreen(device, 824,1988,(76,175,80))

# We should be in a call now
MonkeyRunner.sleep(3)
monkeylib.takeScreenshot(device, "/home/laurenz/aftercall.png")
