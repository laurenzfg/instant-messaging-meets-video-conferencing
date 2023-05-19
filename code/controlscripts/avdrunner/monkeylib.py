# Imports the monkeyrunner modules used by this program
from com.android.monkeyrunner import MonkeyRunner

def pressButtonAsSoonAsItIsOnScreen(device, x, y, buttonColor):
    while 1 == 1:
        # Take a screenshot
        result = device.takeSnapshot()

        # Check if the check pixel has the desired color. Then, we assume it to be a button
        acceptCallFieldColors = result.getRawPixel(x, y)   
        offset = abs(acceptCallFieldColors[1]-buttonColor[0]) + abs(acceptCallFieldColors[2]-buttonColor[1]) + abs(acceptCallFieldColors[3]-buttonColor[2])

        if offset < 10:
            # we have green button
            device.touch(x, y, "DOWN_AND_UP")
            break

        # we don't have a green button yet
        MonkeyRunner.sleep(1)

def stopAllMessengers(device):
    device.shell("am force-stop com.whatsapp")
    device.shell("am force-stop org.thoughtcrime.securesms")
    device.shell("am force-stop org.telegram.messenger.web")

def forceStopStartActivity(device, package, activity):
    # sets the name of the component to start
    runComponent = package + '/' + activity

    # Force stops the package + Runs the component
    device.shell("am force-stop " + package)
    device.startActivity(component=runComponent)

def takeScreenshot(device, filename):
    screenshot = device.takeSnapshot()

    screenshot.writeToFile(filename, 'png')
