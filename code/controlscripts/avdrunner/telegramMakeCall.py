# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection()

monkeylib.forceStopStartActivity(device, 'org.telegram.messenger.web', 'org.telegram.ui.LaunchActivity')

MonkeyRunner.sleep(2)

# Give Focus
device.touch(0, 0, "DOWN_AND_UP")

# Initiate Call to Last Contact
device.touch(600, 300, "DOWN")
MonkeyRunner.sleep(0.2)
device.touch(600, 300, "UP")
MonkeyRunner.sleep(1.5)

# Press Phone Button
device.touch(875, 150, "DOWN_AND_UP")
MonkeyRunner.sleep(1.5)

# Press Camera Button
device.touch(400, 2150, "DOWN_AND_UP")
MonkeyRunner.sleep(0.5)

# Confirm Camera
device.touch(550, 2050, "DOWN_AND_UP")
MonkeyRunner.sleep(1)

# We should be in a call now
MonkeyRunner.sleep(3)
