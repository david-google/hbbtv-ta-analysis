#!/bin/bash

if (( ${#1} == 0 )); then echo "
# HbbTV TA testing orchestrator, runs QR extraction and detection scripts
# Can pass individual files to script, or run on a whole folder of videos
# Configure script location/python at top; examples for Linux, Mac and Cygwin
#
# Usage:  ./hbbtv_orchestrator.sh <video1.mp4> [<video2.mp4>] ... [videoN.mp4>]
#         ./hbbtv_orchestrator.sh *.mp4
#
# jgupta@google.com - 20220211 - v0.4 - Linux, Mac, Cygwin config examples
"; exit; fi

# script and python location
## Linux or Mac, scripts in the path (default)
QR_DETECTION='basic_qr_detection.py'
TA_ANALYSIS='hbbtv_ta_analysis.py'

## Linux or Mac, scripts in this folder (uncomment following two lines)
#QR_DETECTION='./basic_qr_detection.py'
#TA_ANALYSIS='./hbbtv_ta_analysis.py'

## Cygwin, pre-pend python path (uncomment following lines / adjust folders)
#QR_DETECTION='/cygdrive/c/Python38-32/python3 basic_qr_detection.py'
#TA_ANALYSIS='/cygdrive/c/Python38-32/python3 hbbtv_ta_analysis.py'

echo

# run QR_DETECTION on video files passed and store in CSV files of same name
for file in $@; do
  name=`echo ${file%.*}`
  echo "Running QR detection on $file and storing results in $name.csv ..."
  $QR_DETECTION -v $file >/dev/null 2>&1

  # update list of CSV files
  if (( ${#CSV_LIST} == 0 )); then
    CSV_LIST="$name.csv"
  else
     CSV_LIST="$CSV_LIST $name.csv"
  fi  
done

echo

# run TA_ANALYSIS on all CSV files generated in prior step
echo "Running TA analysis on $CSV_LIST ..."
echo
$TA_ANALYSIS $CSV_LIST
