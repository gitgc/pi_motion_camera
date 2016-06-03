# import the necessary packages
from imutils.video import VideoStream
import datetime
import argparse
import imutils
import time
import warnings
import json
import cv2
from tempimage import TempImage

# Parse arguments from JSON config file
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
args = vars(ap.parse_args())

warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))

# initialize the video stream and allow the cammera sensor to warmup
#vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
vs = VideoStream(usePiCamera=True, framerate=conf["fps"], resolution=tuple(conf["resolution"])).start()
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0

# loop over the frames from the video stream
while True:
    motionDetected = False
	# grab the frame from the threaded video stream and resize it
    # resize the frame, convert it to grayscale, and blur it
    frame = vs.read()
    analysisFrame = imutils.resize(frame, width=conf["opencv_image_width"])
    gray = cv2.cvtColor(analysisFrame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # if the average frame is None, initialize it
    if avg is None:
        print("[INFO] starting background model...")
        avg = gray.copy().astype("float")
        continue

    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    # threshold the delta image, dilate the thresholded image to fill
    # in holes, then find contours on thresholded image
    thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    (_, cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # loop over the contours

    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < conf["min_area"]:
            continue

        motionDetected = True

	# draw the timestamp on the frame
    timestamp = datetime.datetime.now()
    #ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    #cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
    #           0.35, (0, 0, 255), 1)  # Check to see if motion

    if motionDetected:
        # check to see if enough time has passed between uploads
        # if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:

        # increment the motion counter
        motionCounter += 1

        print("Motion Counter:" + str(motionCounter))

        # check to see if the number of frames with consistent motion is
        # high enough
        if motionCounter >= conf["min_motion_frames"]:
            t = TempImage()
            cv2.imwrite(t.path, frame)

            # update the last uploaded timestamp and reset the motion
            # counter
            lastUploaded = timestamp
            motionCounter = 0

    else:
        motionCounter = 0