import os
import platform
import sys

libdir = 'apps/python/hotlap/lib' + '64' if platform.architecture()[0] == '64bit' else ''
sys.path.insert(0, libdir)
os.environ['PATH'] += ';.'

import json

import ac
import acsys

from urllib import request

from sim_info import info

NAME = 'HotLap'
VERSION = 0.1
AGENT = '%s_%f' % (NAME, VERSION)
SIZE = (400, 200)
WINDOW = None
LAP_VALID_INDICATOR = None

DRIVER_ID_SELF = 0

UPDATE_DELTA = 0
UPDATE_THRESHOLD = 1000

TIRES_THRESHOLD = 2
CURRENT_LAP_VALID = True

DRIVER      = ''
TRACK       = ''
CAR         = ''
BEST_LOGGED_LAP = sys.maxsize
LAP_HISTORY = []

LAP_COUNT = 5
LAP_LABELS = []

SERVER = ''

ACTIVE = True

if not SERVER:
    ac.console('Server is unset')

def onActivate():
    global ACTIVE
    ACTIVE = True
    ac.console('Activated')

def onDeactivate():
    global ACTIVE
    ACTIVE = False
    ac.console('Deactivated')

def reportLap(lap_data):
    global AGENT
    data = json.dumps(lap_data)
    req = request.Request(SERVER, data=data.encode('utf8'))
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', AGENT)
    resp = request.urlopen(req)

def getLapData():
    url = '%s?track=%s&car=%s&limit=%d' % (SERVER, TRACK, CAR, LAP_COUNT)
    req = request.Request(url)
    req.add_header('User-Agent', AGENT)
    resp = request.urlopen(req).read().decode('utf8')
    return json.loads(resp)

def msToHumanReadable(millis):
    ms  = int((millis % 1000) / 100)
    sec = int((millis / 1000) % 60)
    min = int((millis / (1000 * 60)) % 60)

    return '%02d:%02d.%03d' % (min, sec, ms)

def refreshLapDisplay():
    global LAP_LABELS, LAP_VALID_INDICATOR
    laps = getLapData()

    i = 0
    while i < len(laps):
        lap = laps[i]
        driver = lap['driver']
        lap_time = msToHumanReadable(lap['lap'])
        lap_label = '%s - %s' % (driver, lap_time)
        ac.setPosition(LAP_LABELS[i], 15, 30 * (i + 1))
        ac.setText(LAP_LABELS[i], lap_label)
        i += 1
    ac.setPosition(LAP_VALID_INDICATOR, 15, 30 * (len(laps) + 1))

def acMain(ac_version):
    global DRIVER, TRACK, CAR, WINDOW, LAP_LABELS, LAP_VALID_INDICATOR

    DRIVER = ac.getDriverName(DRIVER_ID_SELF)
    TRACK  = '%s-%s' % (ac.getTrackName(DRIVER_ID_SELF), ac.getTrackConfiguration(DRIVER_ID_SELF))
    CAR    = ac.getCarName(DRIVER_ID_SELF)

    ac.console('Initialize %s: driver %s on %s in %s' % (NAME, DRIVER, TRACK, CAR))

    WINDOW = ac.newApp(NAME)
    ac.setSize(WINDOW, *SIZE)
    ac.setTitle(NAME)

    if ac.addOnAppActivatedListener(WINDOW, onActivate) == -1:
        ac.console('Failed to add listener activate')
    if ac.addOnAppDismissedListener(WINDOW, onDeactivate) == -1:
        ac.console('Failed to add listener deactivate')

    i = 0
    while i < LAP_COUNT:
        label = ac.addLabel(WINDOW, 'Waiting for lap time...')
        LAP_LABELS.append(label)
        i += 1
    LAP_VALID_INDICATOR = ac.addLabel(WINDOW, 'Clean')
    refreshLapDisplay()

    return NAME

def acUpdate(ms):
    global BEST_LOGGED_LAP, LAP_HISTORY, UPDATE_DELTA, CURRENT_LAP_VALID, LAP_VALID_INDICATOR

    if ACTIVE:
        if CURRENT_LAP_VALID and info.physics.numberOfTyresOut > TIRES_THRESHOLD:
            ac.setText(LAP_VALID_INDICATOR, 'Dirty')
            CURRENT_LAP_VALID = False

        #UPDATE_DELTA += ms
        #if UPDATE_DELTA < UPDATE_THRESHOLD:
        #    return
        #UPDATE_DELTA = 0

        last_lap = ac.getCarState(DRIVER_ID_SELF, acsys.CS.LastLap)
        valid = CURRENT_LAP_VALID and not ac.getCarState(DRIVER_ID_SELF, acsys.CS.LapInvalidated)

        if last_lap and (not LAP_HISTORY or not last_lap == LAP_HISTORY[-1]):
            ac.console('Last lap: %s%s' % (last_lap, '' if valid else ' (invalid)'))

            reportLap({'driver': DRIVER,
                       'track': TRACK,
                       'car': CAR,
                       'lap': last_lap})

            refreshLapDisplay()
            
            # reset lap tracking
            ac.setText(LAP_VALID_INDICATOR, 'Clean')
            CURRENT_LAP_VALID = True
            LAP_HISTORY.append(last_lap)
