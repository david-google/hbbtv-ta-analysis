# hbbtv-ta
Evaluates HbbTV-TA transistion times based on captured QR code sequences and is designed to process video recordings of TVs running the DTG's HbbTV-TA demonstration application and test stream (QR code variant) made with a fixed camera.

## Scripts

This project comprises three scripts, two using Python 3 and one using Bash. These scripts also rely on the presence of the Zbar QR code detection software. See **INSTALL.txt** for installation and usage instructions. These scripts have been successfully used with Mac, Linux and Windows (using Cygwin).

### basic_qr_detection.py

*Author: nicholas.frame@tpv-tech.com*

This script takes an MP4 video file as input and outputs a CSV file containing all QR codes detected, along with the timecodes.

% basic_qr_detection.py
usage: basic_qr_detection.py [-h] -v VIDEO
basic_qr_detection.py: error: the following arguments are required: -v/--video

### hbbtv_ta_analysis.py

*Authors: jgupta@google.com*
*Reviewer: duhlmann@google.com*

This script takes one or more CSV files produced by **basic_qr_detection.py** and produces a summary report showing which sections of ads and content were detected along with the timings of any switches from broadcast to broadband content and back again.

% hbbtv_ta_analysis.py 
usage: hbbtv_ta_analysis.py [-h] CSV [CSV ...]
hbbtv_ta_analysis.py: error: the following arguments are required: CSV

### hbbtv_orchestrator.sh

Author: jgupta@google.com

\# run testing orchestrator across all mp4 files (QR code detection & analysis)
% hbbtv_orchestrator.sh *.mp4

## Expected usage

Typical usage will be:

\# run testing orchestrator across all mp4 files (QR code detection & analysis)
% hbbtv_orchestrator.sh *.mp4

\# re-run analysis script across existing QR code CSV files
% hbbtv_ta_analysis.py *.csv

It can be convenient to re-run the analysis on a set or subset of files in order to create a specific report (e.g. for a set of devices, a specific manufacturer, etc.), or alternatively to re-run the analysis after having set a different set of quality thresholds within the **hbbtv_ta_analysis.py**.
