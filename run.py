#!/usr/bin/python3

#python v3.6
import cv2 #v4.1.0
import numpy #1.16.3
import time, argparse, os, sys, csv
import datetime
from tracker import Tracker
from imutils import perspective #0.5.2


parser = argparse.ArgumentParser(description="Fish Tracker")
parser.add_argument("-s", "--source", type=str, metavar="source", help="source file path", required=True)
parser.add_argument("-b", "--background", type=str, metavar="background image filepath", help="use background image for background subtraction")
format_group = parser.add_mutually_exclusive_group()
format_group.add_argument("-v", "--video", type=str, metavar="file output", help="save as video to output file path")
format_group.add_argument("-f", "--frames", type=str, metavar="folder output", help="save as frames to output folder path")
parser.add_argument("-c", "--calibrate", help="only perform calibration of running average", action="store_true")
parser.add_argument("--alpha", type=float, metavar="default=0.01", help="set alpha for running average", default=0.01)
parser.add_argument("--medianblur", type=int, metavar="default=7", help="set value for medianblur, value must be an odd number", default=7)
parser.add_argument("--threshold", type=int, metavar="default=30", help="set value for threshold", default=30)
parser.add_argument("--contour", type=int, metavar="default=1", help="any contour smaller than defined size would be ignored", default=0)
parser.add_argument("--foreground", help="only show foreground detection", action="store_true")
parser.add_argument("--area", type=float, metavar="area of reference object", help="area of reference object")
parser.add_argument("--diameter", type=float, metavar="diameter of reference object", help="diameter of reference object")
parser.add_argument("--output", type=str, metavar="default=./data.csv", help="output filepath of data file", default="./data.csv")
parser.add_argument("--silent", help="silent mode", action="store_true")
parser.add_argument("--debug", help="show contours", action="store_true")
args = parser.parse_args()

# define colors as BGR format as opencv is in BGR
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 230)  

if not os.path.exists(args.source):
    print("Error: source path does not exist")
    sys.exit()

# video capture instance
capture = cv2.VideoCapture(args.source)

# video properties
framenum = int(capture.get(7))
fps = int(capture.get(5))
fourcc = int(capture.get(6)) # codec #FIXME: fix codec to fall back into a default encoding
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')
width = int(capture.get(3))
height = int(capture.get(4))
calibrate = False # boolean to determine need for calibration

# video write instance
if not args.video == None:
    if args.foreground:
        videowriter = cv2.VideoWriter(args.video, fourcc, fps, (width, height), False)
    else:
        videowriter = cv2.VideoWriter(args.video, fourcc, fps, (width, height))

if not args.frames == None:
    if os.path.exists(args.frames):
        if not os.path.isdir(args.frames):
            print("Error: folder path not a directory")
            sys.exit()
    else:
        try:
            os.mkdir(args.frames)
        except OSError:
            print("Unable to create directory")
            sys.exit()

# obtain calibrated background via running average
if not args.background == None:
    if not os.path.exists(args.background):
        print("Error: background image filepath does not exist")
        sys.exit()
    else:
        background = cv2.imread(args.background)
else:
    calibrate = True

if not capture.isOpened(): # check if capture stream is opened properly
    print("Error: file cannot be read")
    sys.exit()

#print video properties
# print("Frames:", framenum)
print("FPS:", fps)
print("Size: %ix%i" % (width,height))

# Track time elapsed & tracking frame count
print("processing...")
count = 0
start = time.time()
diameter_unit = "px"
area_unit = "px"

# calibrate running average
if calibrate:
    capture2 = cv2.VideoCapture(args.source)
    background = numpy.zeros((height, width, 3), numpy.float32) # initialize empty matrix
    while (capture2.isOpened()):
        ret, frame = capture2.read()
        if ret:
            cv2.accumulateWeighted(frame, background, args.alpha) # caculate average using accumulated weighted average
        else:
            break
    background = cv2.convertScaleAbs(background)
    cv2.imwrite("./background.jpg", background)
    capture2.release()
    if args.calibrate:
        sys.exit()

background = cv2.medianBlur(background, 7)
tracker = Tracker()
data = []

# process source video
while (capture.isOpened()):

    ret, frame = capture.read() # read frames, ret=true if read success
    
    if ret:
        
        # calculate ratio of diameters to pixel using reference object
        if count == 0:
            frame2 = frame.copy()
            ratio = 1
            refimg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            refimg = cv2.GaussianBlur(refimg, (7, 7), 0)
            refimg = cv2.Canny(refimg, args.threshold, 70)
            refimg = cv2.dilate(refimg, None, iterations=1)
            refimg = cv2.erode(refimg, None, iterations=1)
            cnts, _ = cv2.findContours(refimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not args.area == None:
                moment = cv2.moments(cnts[0])
                ratio = args.area/moment["m00"]
                tracker.area_ratio = ratio
                area_unit = "mm^2"
            if not args.diameter == None:
                bound = cv2.minAreaRect(cnts[0])
                bound = cv2.boxPoints(bound)
                bound = numpy.array(bound, dtype="int")
                bound = perspective.order_points(bound)
                cv2.drawContours(frame2, [bound.astype("int")], -1, RED, 2)
                (tl, tr, br, bl) = bound
                tltrX = int((tl[0] + tr[0]) * 0.5)
                tltrY = int((tl[1] + tr[1]) * 0.5)
                blbrX = int((bl[0] + br[0]) * 0.5)
                blbrY = int((bl[1] + br[1]) * 0.5)
                cv2.line(frame2, (tltrX, tltrY), (blbrX, blbrY), BLUE, 2)
                distance = numpy.sqrt(((tltrX-blbrX)**2) + ((tltrY-blbrY)**2))
                ratio = args.diameter/distance
                tracker.diameter_ratio = ratio
                diameter_unit = "mm"
                if args.debug:
                    cv2.imwrite("test.bmp", frame2)

        # process background substraction
        blur = cv2.medianBlur(frame, 7) # median blur to remove noise
        foreground = cv2.absdiff(blur, background) # subtract background
        foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2GRAY) # turn into grayscale channel cv_8uc1
        result = cv2.threshold(foreground, args.threshold, 255, cv2.THRESH_BINARY)[1] # threshold

        # contour tracking
        contours, hierachy = cv2.findContours(result, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        index = 0
        centroids = []
        for contour in contours:
            moment = cv2.moments(contour)
            if moment["m00"] > args.contour: # objects with area more than area threshold detected
                if args.debug:
                    cv2.drawContours(frame, contours, index, GREEN, 2) # draw contour in frame, draw only if detected under contour threshold
                x = int(moment["m10"]/moment["m00"])
                y = int(moment["m01"]/moment["m00"])
                center = (x, y) # calculate center of contour
                centroids.append((contour, center, moment["m00"], 0))
            index += 1

        tracker.Update(centroids, (count/fps))

        fishes = tracker.fishes
        
        # exit program if there are no fishes detected
        if len(fishes) is 0:
            print("No fish detected")
            sys.exit()

        total_avg_speed = 0
        total_area = 0

        for i in range(len(fishes)):
            fish = tracker.fishes[i]
            center = fish.centroid
            if args.debug:
                cv2.putText(frame,"id: % i" % fish.id, center, cv2.FONT_HERSHEY_SIMPLEX, 1, WHITE, 3)
            total_avg_speed += fish.speed # calculate total speed
            total_area += fish.size # calculate total size

        average_speed = total_avg_speed/len(fishes) # calculate average speed
        average_area = total_area/len(fishes) # calculate average size

        total_diameter = 0

        # create bounding boxes for each object detected and calculate diameter of object
        for i in range(len(fishes)):
            diameter = 0
            fish = tracker.fishes[i]
            contour = fish.contour
            bound = cv2.minAreaRect(contour)
            bound = cv2.boxPoints(bound)
            bound = numpy.array(bound, dtype="int")
            bound = perspective.order_points(bound)
            if args.debug:
                cv2.drawContours(frame, [bound.astype("int")], -1, GREEN, 2)

            # points on object boundary
            (tl, tr, br, bl) = bound
            point1 = (int(tl[0]), int(tl[1]))
            point2 = (int(tr[0]), int(tr[1]))
            point3 = (int(bl[0]), int(bl[1]))
            point4 = (int(br[0]), int(br[1]))

            if args.debug:
                cv2.circle(frame, point1, 5, BLUE, -1)
                cv2.circle(frame, point2, 5, BLUE, -1)
                cv2.circle(frame, point3, 5, RED, -1)
                cv2.circle(frame, point4, 5, RED, -1)

            # coordinates for middle point of bottom left-right and top left-right
            tltrX = int((tl[0] + tr[0]) * 0.5)
            tltrY = int((tl[1] + tr[1]) * 0.5)
            blbrX = int((bl[0] + br[0]) * 0.5)
            blbrY = int((bl[1] + br[1]) * 0.5)

            if args.debug:
                cv2.circle(frame, (tltrX, tltrY), 5, YELLOW, -1)
                cv2.circle(frame, (blbrX, blbrY), 5, YELLOW, -1)
            
            diameter1 = numpy.sqrt(((tltrX-blbrX)**2) + ((tltrY-blbrY)**2))

            # coordinates for middle point of right top-bottom and left top-bottom
            tlblX = int((tl[0] + bl[0]) * 0.5)
            tlblY = int((tl[1] + bl[1]) * 0.5)
            trbrX = int((tr[0] + br[0]) * 0.5)
            trbrY = int((tr[1] + br[1]) * 0.5)

            if args.debug:
                cv2.circle(frame, (tlblX, tlblY), 5, YELLOW, -1)
                cv2.circle(frame, (trbrX, trbrY), 5, YELLOW, -1)
            
            diameter2 = numpy.sqrt(((tlblX-trbrX)**2) + ((tlblY-trbrY)**2))

            # the longest diameter of object means head to tail
            if diameter1 > diameter2:
                diameter = diameter1
                if args.debug:
                    cv2.line(frame, (tltrX, tltrY), (blbrX, blbrY), YELLOW, 2)
            else:
                diameter = diameter2
                if args.debug:
                    cv2.line(frame, (tlblX, tlblY), (trbrX, trbrY), YELLOW, 2)

            fish.diameter = diameter
            total_diameter += diameter # calculate total diameter

        average_diameter = total_diameter/len(fishes) # calculate average diameter

        text_width = int(0.10 * width)
        text_height = int(0.75 * height)

        num_of_fishes = len(fishes)
        cluster = tracker.cluster * tracker.diameter_ratio
        speed = average_speed * tracker.diameter_ratio
        diameter = average_diameter* tracker.diameter_ratio
        area = average_area * tracker.area_ratio

        cv2.putText(frame, "fishes: %i" % (num_of_fishes), (text_width, text_height), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 3)
        cv2.putText(frame, "cluster: %i" % (cluster), (text_width, text_height+50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 3)
        cv2.putText(frame, "average speed: %i %s/s" % (speed, diameter_unit), (text_width, text_height+100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 3)
        cv2.putText(frame, "average diameter: %i %s" % (diameter, diameter_unit), (text_width, text_height+150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 3)
        cv2.putText(frame, "average area: %i %s" % (area, area_unit), (text_width, text_height+200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 3)
        # datetime.datetime.now()
        timestamp =  datetime.datetime.now()

        data.append([num_of_fishes, timestamp ,cluster, speed, diameter, area])

        # resize frame to fit pc screen
        scale = 0.6
        resize_width = int(scale*width)
        resize_height = int(scale*height)

        resize_frame = cv2.resize(frame, (resize_width, resize_height))
        resize_result = cv2.resize(result, (resize_width, resize_height))

        # Write to medium
        if not args.video == None: # write to video
            if args.foreground:
                videowriter.write(result)
            else:
                videowriter.write(frame)
        elif not args.frames == None: #  write to frames
            cv2.imwrite(args.frames + ("/frame_%i.jpg" % count), frame)
        elif args.silent:
            print(count)
            pass
        else: # show in window
            cv2.imshow("foreground", resize_result)
            cv2.imshow("frame", resize_frame)
			
        count +=1
    
    else:
        break # break when reach end of src video

    if cv2.waitKey(1) & 0xFF == ord('q'): #delay by 1ms, press 'q' to exit
        break

# write to csv file
file = open(args.output, mode="w")
writer = csv.writer(file, delimiter=",")
for row in data:
    writer.writerow(row)

end = time.time()
print("time elapsed: %i secs" % (end-start))

capture.release() # release video capture instance
cv2.destroyAllWindows() # close all windows

# release video instance
if not args.video == None:
    videowriter.release()
    
