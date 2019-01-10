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
SIZE = (400, 200)

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
    data = json.dumps(lap_data)
    req = request.Request(SERVER, data=data.encode('utf8'))
    resp = request.urlopen(req)

def getLapData():
    url = SERVER + '?track=' + TRACK + '&car=' + CAR
    req = request.Request(url)
    resp = request.urlopen(req).read().decode('utf8')
    return json.loads(resp)

def msToHumanReadable(millis):
    ms  = int(millis % 1000) / 100
    sec = int(millis / 1000) % 60
    min = int(millis / (1000 * 60)) % 60

    return '{:02d}:{:02d}.{:03d}'.format(min, sec, ms)

def refreshLapDisplay(lap_list):
    laps = getLapData()

    for lap in laps:
        driver = lap['driver']
        lap_time = msToHumanReadable(lap['lap'])
        lap_label = '{} - {}'.format(driver, lap_time)
        ac.addItem(lap_list, lap_label)

def acMain(ac_version):
    global DRIVER, TRACK, CAR

    DRIVER     = ac.getDriverName(DRIVER_ID_SELF)
    TRACK      = ac.getTrackName(DRIVER_ID_SELF) + '-' + ac.getTrackConfiguration(DRIVER_ID_SELF)
    CAR        = ac.getCarName(DRIVER_ID_SELF)

    ac.console('Initialize {}: driver {} on {} in {}'.format(NAME, DRIVER, TRACK, CAR))

    window = ac.newApp(NAME)
    ac.setSize(window, *SIZE)
    ac.setTitle(NAME)

    if ac.addOnAppActivatedListener(window, onActivate) == -1:
        ac.console('Failed to add listener activate')
    if ac.addOnAppDismissedListener(window, onDeactivate) == -1:
        ac.console('Failed to add listener deactivate')

    reportLap({'driver': DRIVER,
               'track': TRACK,
               'track_conf': TRACK_CONF,
               'car': CAR,
               'lap': 300000})

    lap_list = ac.addListBox(window, 'Laps')
    refreshLapDisplay(lap_list)

    return NAME

def acUpdate(ms):
    global BEST_LOGGED_LAP, LAP_HISTORY, UPDATE_DELTA, CURRENT_LAP_VALID

    if ACTIVE:
        if CURRENT_LAP_VALID and info.physics.numberOfTyresOut > TIRES_THRESHOLD:
            ac.console('current lap invalid')
            CURRENT_LAP_VALID = False

        #UPDATE_DELTA += ms
        #if UPDATE_DELTA < UPDATE_THRESHOLD:
        #    return
        #UPDATE_DELTA = 0

        last_lap = ac.getCarState(DRIVER_ID_SELF, acsys.CS.LastLap)
        valid = CURRENT_LAP_VALID and not ac.getCarState(DRIVER_ID_SELF, acsys.CS.LapInvalidated)

        if last_lap and (not LAP_HISTORY or not last_lap == LAP_HISTORY[-1]):
            refreshLapDisplay()
            if last_lap < BEST_LOGGED_LAP and valid:

                ac.console('New record: {}'.format(last_lap))
                reportLap({'driver': DRIVER,
                           'track': TRACK,
                           'track_conf': TRACK_CONF,
                           'car': CAR,
                           'lap': last_lap})

                BEST_LOGGED_LAP = last_lap
            else:
                ac.console('Last lap: {}{}'.format(last_lap, '' if valid else ' (invalid)'))
            # reset lap tracking
            CURRENT_LAP_VALID = True
            LAP_HISTORY.append(last_lap)
