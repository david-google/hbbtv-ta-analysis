#!/bin/bash

if (( ${#1} == 0 )); then echo "
# HbbTV TA testing orchestrator, runs QR extraction and detection scripts
# Can pass individual files to script, or run on a whole folder of videos
# Configure script location at top
#
# Usage:  ./hbbtv_orchestrator.sh <video1.mp4> [<video2.mp4>] ... [videoN.mp4>]
#         ./hbbtv_orchestrator.sh *.mp4
#
# jgupta@google.com - 20220204 - v0.3 - provides more info on console
"; exit; fi

# script location - either put in Path or use ./ to run in current directory
QR_DETECTION='basic_qr_detection.py'
TA_ANALYSIS='hbbtv_ta_analysis.py'

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
