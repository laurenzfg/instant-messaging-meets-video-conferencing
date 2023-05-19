# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection()

monkeylib.forceStopStartActivity(device, 'com.whatsapp', 'com.whatsapp.Main')

MonkeyRunner.sleep(2)

# Give Focus
device.touch(0, 0, "DOWN_AND_UP")

# Initiate Call to Last Contact
device.touch(444, 444, "DOWN_AND_UP")
MonkeyRunner.sleep(1.5)

device.touch(770, 140, "DOWN_AND_UP")
MonkeyRunner.sleep(1.5)

device.touch(900, 1200, "DOWN_AND_UP")


# We should be in a call now
MonkeyRunner.sleep(3)
monkeylib.takeScreenshot(device, "/home/laurenz/aftercall.png")
