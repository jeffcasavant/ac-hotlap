import os
import platform
import sys

libdir = 'apps/python/hotlap/lib' + '64' if platform.architecture()[0] == '64bit' else ''
sys.path.insert(0, libdir)
os.environ['PATH'] += ';.'

import json
import urllib.request as urllib2

import ac
import acsys

from sim_info import info

NAME = 'HotLap'
SIZE = (200, 200)

DRIVER_ID_SELF = 0

UPDATE_DELTA = 0
UPDATE_THRESHOLD = 1000

TIRES_THRESHOLD = 2
CURRENT_LAP_VALID = True

DRIVER      = ''
TRACK       = ''
TRACK_CONF  = ''
CAR         = ''
BEST_LOGGED_LAP = sys.maxsize
LAP_HISTORY = []

SERVER = ''

ACTIVE = True

def onActivate():
    global ACTIVE
    ACTIVE = True

def onDeactivate():
    global ACTIVE
    ACTIVE = False

def acMain(ac_version):
    global DRIVER, TRACK, CAR

    DRIVER     = ac.getDriverName(DRIVER_ID_SELF)
    TRACK      = ac.getTrackName(DRIVER_ID_SELF)
    TRACK_CONF = ac.getTrackConfiguration(DRIVER_ID_SELF)
    CAR        = ac.getCarName(DRIVER_ID_SELF)

    ac.console('Initialize {}: driver {} on {} in {}'.format(NAME, DRIVER, TRACK, CAR))

    window = ac.newApp(NAME)
    ac.setSize(window, *SIZE)
    ac.setTitle(NAME)

    if ac.addOnAppActivatedListener(window, onActivate) == -1:
        ac.console('Failed to add listener activate')
    if ac.addOnAppDismissedListener(window, onDeactivate) == -1:
        ac.console('Failed to add listener deactivate')

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
            if last_lap < BEST_LOGGED_LAP and valid:

                ac.console('New record: {}'.format(last_lap))

                req = urllib2.Request(SERVER,
                                      data=json.dumps({'driver': DRIVER,
                                                       'track': TRACK,
                                                       'track_conf': TRACK_CONF,
                                                       'car': CAR,
                                                       'lap': last_lap}))
                resp = urllib2.urlopen(req)
                ac.console(resp)

                BEST_LOGGED_LAP = last_lap
            else:
                ac.console('Last lap: {}{}'.format(last_lap, '' if valid else ' (invalid)'))
            # reset lap tracking
            CURRENT_LAP_VALID = True
            LAP_HISTORY.append(last_lap)
