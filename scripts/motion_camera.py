from gpiozero import MotionSensor
from subprocess import call
from datetime import datetime
import os
import picamera
import argparse
import json
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--server')
parser.add_argument('--camera_name')
parser.add_argument('--location')
parser.add_argument('--output_dir')
args = parser.parse_args()

output_dir = args.output_dir
eventPostUrl = args.server
cameraName = args.camera_name
location = args.location

print("Writing images to " + output_dir)
print("Posting data to " + eventPostUrl)

pir = MotionSensor(4)
camera = picamera.PiCamera()
camera.resolution = camera.MAX_RESOLUTION
camera.led = False
motionActive = False
imageList = []

def getFileName():
    return "/capture-" + datetime.now().strftime("%Y%m%d-%H%M%S.%f") + ".jpg"

def getFilePath(fileName):
    return output_dir + "/" + fileName

def captureUSBImage():
    call(['/usr/bin/fswebcam -r 1920x1080 ' + getFilePath()], shell=True, cwd=output_dir)

def capturePiImage():
    fileName = getFileName()
    filePath = getFilePath(fileName)

    image = {}
    image['name'] = fileName
    image['path'] = filePath
    image['date'] = datetime.now().isoformat()

    camera.capture(getFilePath())
    imageList.append(image)

def motionDetected():
    global motionActive
    motionActive = True

def noMotionDetected():
    global motionActive
    global imageList
    motionActive = False
    postImages(imageList)
    imageList = []

def postImages(imageList):
    if len(imageList) > 0:
        data = {}
        data['cameraName'] = cameraName
        data['cameraLocation'] = location
        data['date'] = datetime.now().isoformat()
        data['images'] = imageList

        json_data = json.dumps(data).encode('utf8')

        req = urllib.request.Request(eventPostUrl,
                                 data=json_data,
                                 headers={'content-type': 'application/json'})
        response = urllib.request.urlopen(req)

pir.when_motion = motionDetected
pir.when_no_motion = noMotionDetected

while True:
    pir.wait_for_motion(0.1)
    if motionActive:
        capturePiImage()
