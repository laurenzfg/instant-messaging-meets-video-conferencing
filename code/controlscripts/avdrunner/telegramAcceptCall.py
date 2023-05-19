# WARN THIS IS PYTHON 2.7

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
import monkeylib

# Connects to the current device, returning a MonkeyDevice object
device = MonkeyRunner.waitForConnection()

monkeylib.forceStopStartActivity(device, 'org.telegram.messenger.web', 'org.telegram.ui.LaunchActivity')

MonkeyRunner.sleep(3)

# Give Focus
device.touch(0, 0, "DOWN_AND_UP")

monkeylib.pressButtonAsSoonAsItIsOnScreen(device, 600,200,(40,46,49))
MonkeyRunner.sleep(1)

device.drag((900,2000),(500,2000),1.0,13)

MonkeyRunner.sleep(2)
# Press Camera Button
device.touch(400, 2150, "DOWN_AND_UP")
MonkeyRunner.sleep(0.5)

# Confirm Camera
device.touch(550, 2050, "DOWN_AND_UP")
