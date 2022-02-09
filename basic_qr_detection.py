#!/usr/bin/python3

import argparse
import csv
import cv2
import imutils
import datetime

from pathlib import Path
from pyzbar import pyzbar

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", required=True, help="Video file containing the QR codes")
args = vars(ap.parse_args())

video_path = Path(args["video"])

# initialise video input
vid = cv2.VideoCapture(str(video_path))

# determine fps and frame duration
framerate = vid.get(cv2.CAP_PROP_FPS)
frame_duration = round(1/framerate,10)

# set initial video position
frame_count = 0
frame_pts = 0

# initialise results and default margin for area used to detect QR code
res = dict()
last_barcode = ''
max_frame_nb_reached = 0
first_frame_nb = 0
frame_nb = 0
frame_timestamp = "00:00:00.000"
margin = 225

# read frames until entire video has been parsed
while True:
	# read frame
	_, frame = vid.read()
	
	# stop when end of video is reached
	if frame is None:
		break
	
	# get width + height
	#frame_height, frame_width, _ = frame.shape
	
	# downscale the input resolution to 1080p
	frame_width = 1920
	frame_height = 1080
	dres_frame = cv2.resize(frame, (frame_width, frame_height))
	
	# calculate approximate qr code area
	qr_area_topleft_x = int(frame_width * 0.1)
	qr_area_topleft_y = int(frame_height/2 - frame_height*0.25 - margin/2)
	qr_area_bottomright_x = int(frame_width * 0.1 + 2*frame_height*0.25 + margin)
	qr_area_bottomright_y = int(frame_height/2 + frame_height*0.25 + margin/2)
	
	# extract image containing qr code area
	image = dres_frame[qr_area_topleft_y:qr_area_bottomright_y,qr_area_topleft_x:qr_area_bottomright_x]
	
	# convert image to grayscale
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	
	# inverse colours to enable detection of inverted QR codes
	invBlackAndWhiteImage = cv2.bitwise_not(gray)
	
	# detect and decode the QR codes in the image
	barcodes = pyzbar.decode(invBlackAndWhiteImage)
	
	# calculate reference wallclock time based on video timecode
	timecode = '{:02d}:{:02d}:{:06.3f}'.format(int(frame_pts/3600), int(frame_pts/60), frame_pts%60)
	padded_frame = str(frame_count).zfill(7)			
	frame_pts = round(frame_pts+frame_duration,10)
		
	# loop over the detected barcodes
	if barcodes:
		bcs = list()
		for barcode in barcodes:
			if barcode.type == 'QRCODE':
				barcode_data = barcode.data.decode("utf-8")
				if len(barcode_data.split(';')) == 4:
					frame_timestamp = barcode_data.split(';')[1]
					frame_nb = int(eval(barcode_data.split(';')[2].lstrip('0')))
					bcs.append([barcode_data.split(';')[0],frame_timestamp,frame_nb])
				else:
					bcs.append(['CONFIG',frame_timestamp,frame_nb,barcode_data])
		bcs_sorted = list(sorted(bcs, key=lambda bc: bc[2]))
		
		i=1
		for bc in bcs_sorted:
			# IMPORTANT: this is only a VERY rudimentary classiifcation mechanism for quick testing
			# some miscategorisation can occur, so some limited additional analysis of the results will be needed
			diff = "first"
			if last_barcode != '':
				if bc[2] == last_barcode[2] or bc[2] == max_frame_nb_reached:
					diff = "duplicate"
				elif bc[2] == last_barcode[2]+1:
					diff = "next"
				elif bc[2] > last_barcode[2]+1:
					diff = "skipped"
				elif bc[2] < last_barcode[2]+1:
					diff = "inverted"
			
			# exception for config data QR code containing test parameters and DUT user agent)
			if bc[0] == 'CONFIG':
				print("{} [{} @ {}] {}: {} {} {} {}".format(datetime.datetime.now().isoformat(), padded_frame+'-'+str(i), timecode, 'QRCODE', bc[0], bc[1], str(bc[2]), bc[3]))
				res[padded_frame+'-'+str(i)] = {'wallclock':timecode, 'barcode_present':'QRCODE', 'qr_label':bc[0], 'qr_timestamp':bc[1], 'qr_frame':bc[2],'prev_frame_diff':'','config':bc[3]}
			else:
				print("{} [{} @ {}] {}: {} {} {} {}".format(datetime.datetime.now().isoformat(), padded_frame+'-'+str(i), timecode, 'QRCODE', bc[0], bc[1], str(bc[2]), diff))
				res[padded_frame+'-'+str(i)] = {'wallclock':timecode, 'barcode_present':'QRCODE', 'qr_label':bc[0], 'qr_timestamp':bc[1], 'qr_frame':bc[2],'prev_frame_diff':diff,'config':''}
			i+=1
			
			# keep track of first and highest frame numbers detected in current sequence (used for duplicate detection)
			if last_barcode == '':
				first_frame_nb = bc[2]
				max_frame_nb_reached = bc[2]
			last_barcode = bc
			# stream in recording may loop back to first frame
			if (bc[2] < first_frame_nb-3 or bc[2] < 2) and max_frame_nb_reached > 1:
				first_frame_nb = bc[2]
				max_frame_nb_reached = bc[2]
			# in case frame N+1/+2/+3 detected before N at start of recording (due to presence of multiple QR codes on screen)
			elif bc[2] < first_frame_nb and bc[2] < max_frame_nb_reached:
				first_frame_nb = bc[2]
			else:
				max_frame_nb_reached = max(max_frame_nb_reached,bc[2])
	
	else:
		print("{} [{} @ {}] No QR code detected".format(datetime.datetime.now().isoformat(), padded_frame+'-0', timecode))
		res[padded_frame+'-0'] = {'wallclock':timecode, 'barcode_present':'none', 'qr_label':'', 'qr_timestamp':'', 'qr_frame':'','prev_frame_diff':'','config':''}
	
	frame_count += 1

# release the video pointer
vid.release()

# output QR code data to CSV (file will be created OR OVERWRITTEN if it exists)
with open(video_path.stem+'.csv', 'w', newline='') as outfile:
	clWriter = csv.DictWriter(
		outfile,
		fieldnames=['wallclock', 'barcode_present', 'qr_label', 'qr_timestamp', 'qr_frame', 'prev_frame_diff', 'config'],
		extrasaction='ignore', 
		dialect='excel'
		#delimiter=',',
		#quotechar='|',
		#quoting=csv.QUOTE_MINIMAL
	)
	clWriter.writeheader()
	for frame in res:
		clWriter.writerow(res.get(frame))
