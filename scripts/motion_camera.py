from gpiozero import MotionSensor
from subprocess import call
from datetime import datetime
import os
import picamera

output_dir = os.getenv('MOTION_CAMERA_OUTPUT_DIR', '/home/pi/Pictures')
print("Oupting images to " + output_dir)
pir = MotionSensor(4)

camera = picamera.PiCamera()
camera.resolution = camera.MAX_RESOLUTION
camera.led = False

motionActive = False

def getFileName():
    return output_dir + "/capture-" + datetime.now().strftime("%Y%m%d-%H%M%S.%f") + ".jpg"

def captureUSBImage():
    call(['/usr/bin/fswebcam -r 1920x1080 ' + getFileName()], shell=True, cwd=output_dir)

def capturePiImage():
    camera.capture(getFileName())

def motionDetected():
    global motionActive
    motionActive = True

def noMotionDetected():
    global motionActive
    motionActive = False

pir.when_motion = motionDetected
pir.when_no_motion = noMotionDetected

while True:
    pir.wait_for_motion(0.1)
    if motionActive:
        capturePiImage()
