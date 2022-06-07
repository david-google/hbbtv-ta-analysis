#!/usr/bin/python3

# Takes one or more input files and outputs results on the console and also in
# "TA-OUTPUT-YYYYMMDD-hhmmss.csv" file (Note: output files ignored as inputs)
#
# Usage:  ./hbbtv_ta_analysis.py <input1.csv> [<input2.csv>] ... [<inputN.csv>]
#
# jgupta@google.com - 20220607 - v1.4 - allow missing frames at start or end

import argparse, os, csv, re
from datetime import datetime

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

# output file and header
outprefix = 'TA-OUTPUT'
outfile = outprefix + '-' + datetime.today().strftime('%Y%m%d-%H%M%S') + '.csv'
out = open(outfile, 'w')
out.write('Device.name,Device.useragent,Device.overall,Device.reason,')
out.write('Test.result,Test.msg,Test.vtype,Test.tsource,Test.starttime,Test.endtime,Test.taapi,Test.delay,')
out.write('Section.name,Section.result,Section.gap,Section.length,Section.missingstart,Section.missingend,')
out.write('Section.frames,Section.unique,Section.first,Section.last,Section.start,Section.end,Section.inverted')
out.write('\n')

# load test config - ensure to import each set into the dictionary
config = dict()
config[set1['section']] = set1
config[set2['section']] = set2
config[set3['section']] = set3
config[set4['section']] = set4
config[set5['section']] = set5
config[set6['section']] = set6

# section lookup table so can determine section for any QR and frame
# e.g. section['DTG-ADINS-BC'][3751] = 'Broadcast video part 1'
section = dict()
for key in config.keys():
    subsection = dict()
    for frame in range(config[key]['first'],config[key]['last'] + 1):
        subsection[frame] = key
    try:
        section[config[key]['label']].update(subsection)
    except KeyError:
        section[config[key]['label']] = subsection

# input params (CSV files)
parser = argparse.ArgumentParser()
parser.add_argument ('infile', metavar='CSV', nargs='+', type=str, help='data file') 
args = parser.parse_args()

# open each CSV file in turn, process it and output results
for filename in args.infile:
    if filename.find(outprefix) != -1:
        break
    if not os.path.exists(filename):
        print('File not found: %s\n' % filename)
        break        
    with open(filename, mode='r') as csv_file:
        # reset lookup tables for storing facts for each section
        count     = dict()  # number of frames
        inverted  = dict()  # number of inverted frames
        first     = dict()  # first frame number
        last      = dict()  # last frame number
        start     = dict()  # time of first frame
        end       = dict()  # time of last frame
        visited   = dict()  # list of frames visited (calculate unique frames)
        params    = dict()  # test params collected from the CONFIG QR code
        intact    = dict()  # if section is complete, incomplete or unexpected
        gap3dp    = dict()  # section gap in seconds, three decimal places
        len3dp    = dict()  # section length in seconds, three decimal places
        missstart = dict()  # number of frames missing at the start
        missend   = dict()  # number of frames missing at the end
        unique    = dict()  # number of unique frames

        # reset device config, counter and open file
        device = ''
        line_count = 0
        csv_reader = csv.DictReader(csv_file)

        # check each row for QR codes
        for row in csv_reader:
            if line_count == 0:
                line_count += 1

            # skip rows without a qr_frame
            if 'qr_frame' not in row.keys():
                break

            if row['qr_frame']:
                if row['prev_frame_diff'] != 'duplicate':
                    # account for this frame
                    label = row['qr_label']

                    # check for special CONFIG frame
                    if label == 'CONFIG':
                        if not device:
                             device = row['config']
                        # skip forward
                        break
                         
                    # frame number
                    frame = int(row['qr_frame'])
                    if frame in section[label].keys():
                        this_section = section[row['qr_label']][frame]
                        # update counters
                        if this_section in count.keys():
                            count[this_section]+=1
                            visited[this_section].append(frame)

                            # count inverted frames
                            if this_section not in inverted.keys():
                                inverted[this_section] = 0
                            if row['prev_frame_diff'] == 'inverted':
                                inverted[this_section] += 1
                        else:
                            first[this_section] = frame
                            start[this_section] = float(row['wallclock'].replace(':',''))
                            count[this_section] = 1
                            visited[this_section] = [frame]
                        last[this_section] = frame
                        end[this_section] = float(row['wallclock'].replace(':',''))

                else:
                    # grab timestamp of duplicate frame
                    label = row['qr_label']
                    frame = int(row['qr_frame'])
                    if frame in section[label].keys():
                        this_section = section[row['qr_label']][frame]
                        end[this_section] = float(row['wallclock'].replace(':',''))
            line_count += 1

        # output the report
        print ()

        ## test name
        fileparts = filename.split('.')
        print(f'Device Name: "{fileparts[0]}"')

        ## device capabilities
        # device config is a set of name=value pairs ; separated
        # however the last value (useragent) may contain ;, need to handle
        metadata = re.split(';ua=', device)

        if len(metadata) > 1:
            print('Test Params: "%s"' % metadata[0])
            print('User Agent:  "%s"\n' % metadata[1])

            # extract the test params
            testparams = re.split (';', metadata[0])
            params = dict(s.split('=',1) for s in testparams)
            # support empty msg
            if 'msg' not in params.keys():
                params['msg']=''
            outdevice = '%s,\"%s\"' % (fileparts[0], metadata[1])
            outtest = '%s,\"%s\",%s,%s,%s,%s,%s,%s' % (params['result'], params['msg'], params['vtype'],
                params['tsource'], params['starttime'], params['endtime'], params['taapi'], params['delay'])
        else:
            print('Test Config: Not detected\n')
            outdevice = fileparts[0] + ',[not detected]'
            outtest = ',,,,,,,'

        ## frames and timings 
        for key in count.keys():
            # calculate number of unique frames
            visited_set = set(visited[key])
            unique[key] = len(visited_set)

            # fix: populate inverted[key] if missing
            if key not in inverted.keys():
                 inverted[key] = 0

            # show section stats
            print('%s:\t%s frames\t %s unique: %s>%s, time: %s>%s, inverted: %s' % 
                (key, count[key], unique[key], first[key], last[key], start[key], end[key], inverted[key]))
        if count:
            print ()

        ## transitions
        lasttime = 0
        for key in count.keys():
            # calculate any gap between prior and current section
            if (lasttime == 0):
                lasttime = start[key]
            gap = start[key] - lasttime
            length = end[key] - start[key]
            gap3dp[key] = format(gap,'.3f')
            len3dp[key] = format(length,'.3f')

            # determine how complete the section was
            missstart[key] = first[key] - config[key]['first']
            missend[key] = config[key]['last'] - last[key]

            # calculate intact %
            intactcount = 0
            for frame in range(config[key]['first'], config[key]['last'] + 1):
                if frame in visited[key]:
                    intactcount=intactcount+1
            requiredcount = config[key]['last'] - config[key]['first'] + 1
            intactportion = float(intactcount) / float(requiredcount)
            intact3dp = format(intactportion, '.3f')

            # construct result
            if intactportion < config[key]['minimum']:
                intact[key] = 'INCOMPLETE'
            elif intactportion > config[key]['maximum']:
                intact[key] = 'UNEXPECTED'
            else:
                intact[key] = 'COMPLETE'
                # check to see if frame loss at start/end was higher than allowed
                if 'maxloss' in config[key].keys():
                    if missstart[key] > config[key]['maxloss'] or missend[key] > config[key]['maxloss']:
                        intact[key] = 'INCOMPLETE'

            # show section tests results
            print('%s:\t%s\t gap %ss, length %ss, missing start %s, end %s' %
                (key, intact[key], gap3dp[key], len3dp[key], missstart[key], missend[key]))
            lasttime = end[key]  # set the time for next section
        if count:
            print ()

        ## overall result
        overall = 'PASS'
        reason = ''
        for key in config.keys(): 
            # check if we are missing a section which must be present
            if key not in intact.keys() and config[key]['minimum'] > 0:
                overall = 'FAIL'
                if reason != '':
                    reason = reason + '; '
                if key not in intact.keys():
                    reason = reason + key + ' MISSING'
                else:
                    reason = reason + key + ' ' + intact[key]
            # record present sections which were not complete
            elif key in intact.keys() and intact[key] != 'COMPLETE':
                overall = 'FAIL'
                if reason != '':
                    reason = reason + '; '
                reason = reason + key + ' ' + intact[key]
        # if still passing the test, add a reason
        if overall == 'PASS':
            reason = 'All sections COMPLETE'
        print('Overall result:\t%s\t%s' % (overall, reason))

        ## output file
        for key in count.keys():
            # show the device, then the results, then the section stats
            out.write('%s,%s,%s,%s,' % (outdevice, overall, reason, outtest))
            out.write('%s,%s,%s,%s,%s,%s,' % (key, intact[key], gap3dp[key], len3dp[key], missstart[key], missend[key]))
            out.write('%s,%s,%s,%s,%s,%s,%s' % (count[key], unique[key], first[key], last[key], start[key], end[key], inverted[key]))
            out.write('\n')

        # if there are no sections detected, add row to output file
        if len(count) == 0:
            out.write('%s,%s,%s,%s,' % (outdevice, overall, reason, outtest))
            out.write(',,,,,,,,,,,,\n')

        # space between tests
        print ()      

# end
print('Results exported to %s\n' % outfile)
out.close()
