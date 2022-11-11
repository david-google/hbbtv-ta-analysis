# hbbtv-ta
Evaluates HbbTV-TA transistion times based on captured QR code sequences and is designed to process video recordings of TVs running the DTG's HbbTV-TA demonstration application and test stream (QR code variant) made with a fixed camera.

## Scripts

This project comprises three scripts, two using Python 3 and one using Bash. These scripts also rely on the presence of the Zbar QR code detection software. See **INSTALL.txt** for installation and usage instructions. These scripts have been successfully used with Mac, Linux and Windows (using Cygwin).

### basic_qr_detection.py

*Author: nicholas.frame@tpv-tech.com*

This script takes an MP4 video file as input and outputs a CSV file containing all QR codes detected, along with the timecodes, using a Python interface to the Zbar QR code detection software.
```
% basic_qr_detection.py
basic_qr_detection.py: error: the following arguments are required: -v/--video
```
When running the script on an MPG video file (either directly, or via the **hbbtv_orchestrator.sh** script), the script outputs a CSV file, containing timecodes, whether a barcode was present, the label of any barcode, the timestamp of the QR code, whether this QR code has been seen before and whether it is in sequence. In addition, at the end of the stream, the script will pick up the value of the 'config' QR code, which if available, provides additional information about the specific device.
```
% basic_qr_detection.py -v test.mp4
[outputs file test.csv]

% cat test.csv
wallclock,barcode_present,qr_label,qr_timestamp,qr_frame,prev_frame_diff,config
...
00:00:00.834,none,,,,,
00:00:00.843,none,,,,,
00:00:00.851,QRCODE,DTG-AD
00:00:00.851,QRCODE,DTG-ADINS-BC,00:00:18.320,458,skipped,
00:00:00.859,QRCODE,DTG-ADINS-BC,00:00:18.320,458,duplicate,
00:00:00.868,QRCODE,DTG-ADINS-BC,00:00:18.320,458,duplicate,
00:00:00.876,QRCODE,DTG-ADINS-BC,00:00:18.320,458,duplicate,
00:00:00.884,QRCODE,DTG-ADINS-BC,00:00:18.360,459,next,
00:00:00.893,QRCODE,DTG-ADINS-BC,00:00:18.360,459,duplicate,
00:00:00.901,none,,,,,
...
00:06:28.914,QRCODE,CONFIG,00:06:46.520,10163,,"result=2;msg=Test has ended after the switch back to broadcast.;vtype=0;tsource=0;starttime=0;endtime=2;taapi=0;delay=0;ua=Mozilla/5.0 (Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 OPR/40.0.2207.0 OMI/4.9.0.150.DOM3.67 Model/Vestel-MB130 VSTVB MB100 FVC/2.0 (OEM; MB130; ) HbbTV/1.4.1 (; OEM; MB130; 3.22.100.1; _TV_G10_2017; ;) SmartTvA/3.0.0"
...
```
### hbbtv_ta_analysis.py

*Authors: jgupta@google.com*
*Reviewer: duhlmann@google.com*

This script takes one or more CSV files produced by **basic_qr_detection.py** and produces a summary report showing which sections of ads and content were detected along with the timings of any switches from broadcast to broadband content and back again.
```
% hbbtv_ta_analysis.py
usage: hbbtv_ta_analysis.py [-h] CSV [CSV ...]
hbbtv_ta_analysis.py: error: the following arguments are required: CSV
```
If passed one or more CSV files produced by the **basic_qr_detection.py** script (either directly, or via the **hbbtv_orchestrator.sh** script), the script will output the results on the command line in a human readible report and additionally store these results in a CSV file for later processing and analysis.
```
% hbbtv_ta_analysis.py test.csv

Device Name: "test1"
Test Params: "result=2;msg=Test has ended after the switch back to broadcast.;vtype=0;tsource=0;starttime=0;endtime=2;taapi=0;delay=0"
User Agent:  "Mozilla/5.0 (Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 OPR/40.0.2207.0 OMI/4.9.0.150.DOM3.67 Model/Vestel-MB130 VSTVB MB100 FVC/2.0 (OEM; MB130; ) HbbTV/1.4.1 (; OEM; MB130; 3.22.100.1; _TV_G10_2017; ;) SmartTvA/3.0.0"

Digital adverts:	5821 frames	 5821 unique: 1>5822, time: 223.327>616.301, inverted: 0
Broadcast landing:	66 frames	 66 unique: 9895>9960, time: 618.186>620.805, inverted: 0
Broadcast part 2:	110 frames	 110 unique: 9961>10070, time: 620.814>625.201, inverted: 0

Digital adverts:	COMPLETE	 gap 0.000s, length 392.974s, missing start 0, end 3
Broadcast landing:	COMPLETE	 gap 1.885s, length 2.619s, missing start 58, end 0
Broadcast part 2:	COMPLETE	 gap 0.009s, length 4.387s, missing start 0, end 0

Overall result:	FAIL	Broadcast part 1 MISSING

Results exported to TA-OUTPUT-20221103-191311.csv
```
The **hbbtv_ta_analysis.py** can be configured to look for the presence and completeness of various sections within the video file. The scripts are currently configured with the optimal settings determined by the DTG Targeted Ads Substitution working group to maximise the reach of receivers which would pass the test at an 'acceptable user experience' (defined by the group to be losing not more than 1 second of content at the start or end of the ad break).
```
# test config: one set for each section, sections in order frames may appear
set1 = {
    'section':  'Broadcast part 1',
    'label':    'DTG-ADINS-BC',
    'first':    3650,
    'last':     4011,
    'minimum':  0.95,   # allow 18 missing frames for a successful test
    'maximum':  1,
    'maxloss':  10      # allow max 10 frames missing at start or end
    }
set2 = {
    'section':  'Broadcast take-off',
    'label':    'DTG-ADINS-BC',
    'first':    4012,
    'last':     4016,
    'minimum':  0,
    'maximum':  1
    }
set3 = {
    'section':  'Broadcast adverts',
    'label':    'DTG-ADINS-BC',
    'first':    4017,
    'last':     9836,
    'minimum':  0,
    'maximum':  0
    }
set4 = {
    'section':  'Digital adverts',
    'label':    'DTG-ADINS-BB',
    'first':    1,
    'last':     5825,
    'minimum':  0.995,  # allow 29 missing frames for a successful test
    'maximum':  1,
    'maxloss':  10      # allow max 10 frames missing at start or end
    }
set5 = {
    'section':  'Broadcast landing',
    'label':    'DTG-ADINS-BC',
    'first':    9837,
    'last':     9960,
    'minimum':  0,
    'maximum':  1
    }
set6 = {
    'section':  'Broadcast part 2',
    'label':    'DTG-ADINS-BC',
    'first':    9961,
    'last':     10070,
    'minimum':  0.95,   # allow 5 missing frames for a successful test
    'maximum':  1
    }
```
The parameters are defined as follows:
```
'section' is a human readible name for the content or ads section, to be displayed in the report
'label' is the label name encoded in the QR code in the test transport stream or ad stream video
'first' is the ID of the first frame within that section
'last' is the ID of the last frame within that section
'minimum' is a value between 0 and 1 defining how much of the section required for a passing test (e.g. 1 every frame would be required)
'maximum' is a value between 0 and 1 defining how much of the section required for a passing test (e.g. 0 no frames are required)
'maxloss' is an optional parameter to define the maximum number of frames that can be missing from the start or end of a section
```
The **'minimum'**, **'maximum'** and **'maxloss'** paramters are used to set the thresholds which apply to each section in order for it to be considered a pass or a fail for each test. Any test where all sections pass is considered an overall passing test. These threshold parameters can be used together, e.g. for the **'Broadcast landing'** section above, a **'minimum'** of **0** and a **'maximum'** of **1** means the section is optional.

### hbbtv_orchestrator.sh

Author: jgupta@google.com
```
# run testing orchestrator across all mp4 files (QR code detection & analysis)
% hbbtv_orchestrator.sh *.mp4
```
## Expected usage

Typical usage will be:
```
# run testing orchestrator across all mp4 files (QR code detection & analysis)
% hbbtv_orchestrator.sh *.mp4

# re-run analysis script across existing QR code CSV files
% hbbtv_ta_analysis.py *.csv
```
It can be convenient to re-run the analysis on a set or subset of files in order to create a specific report (e.g. for a set of devices, a specific manufacturer, etc.), or alternatively to re-run the analysis after having set a different set of quality thresholds within the **hbbtv_ta_analysis.py**.
