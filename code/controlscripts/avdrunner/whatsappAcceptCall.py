# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection()

monkeylib.forceStopStartActivity(device, 'com.whatsapp', 'com.whatsapp.Main')

# Give Focus
device.touch(0, 0, "DOWN_AND_UP")

monkeylib.pressButtonAsSoonAsItIsOnScreen(device, 600,100,(31,168,85))
MonkeyRunner.sleep(1)
device.drag((540,2093),(540,1000),1.0,13)

# We should be in a call now
MonkeyRunner.sleep(3)
monkeylib.takeScreenshot(device, "/home/laurenz/aftercall.png")
