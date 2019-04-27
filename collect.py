#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
SYNOPSIS

    python collect.py [-h,--help] [-l,--log] [--debug]

DESCRIPTION

    A python application which collects results of an iRacing user.

EXAMPLES

    python collect.py -u "<your iracing username>" -p "<your iracing password>" --test

AUTHOR

    Robert Crouch (rob.crouch@gmail.com)

VERSION

    $Id$
"""

__program__ = "collect-results"
__author__ = "Robert Crouch (rob.crouch@gmail.com)"
__copyright__ = "Copyright (C) 2018- Robert Crouch"
__license__ = "MIT"
__version__ = "v0.190428.1"

import os
import sys
import argparse
import datetime
import logging, logging.handlers
import threading
import queue as queue

from ir_webstats_rc import constants as ct
from ir_webstats_rc.client import iRWebStats
from ir_webstats_rc.util import clean

from db_models import *

lap_flags = {
    0: "clean_laps",
    2: "pitted",
    4: "off_tracks",
    8: "black_flags",
    32: "contacts",
    64: "car_contacts",
    128: "lost_controls",
    2048: "tows"
}

def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=70):
    """Call in a loop to create terminal progress bar """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def print_counting(count, prefix='', suffix='', finished=False):
    """Call in a loop to create terminal count update """

    sys.stdout.write('\r%s %s %s' % (prefix, count, suffix)),

    if finished:
        sys.stdout.write('\n')
    sys.stdout.flush()

class ExThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__status_queue = queue.Queue()

    def run_with_exception(self):
        """This method should be overriden."""
        raise NotImplementedError

    def run(self):
        """This method should NOT be overriden."""
        try:
            self.run_with_exception()
        except BaseException:
            self.__status_queue.put(sys.exc_info())
        self.__status_queue.put(None)

    def wait_for_exc_info(self):
        return self.__status_queue.get()

    def join_with_exception(self):
        ex_info = self.wait_for_exc_info()
        if ex_info is None:
            return
        else:
            raise ex_info[1]


class MyException(Exception):
    pass


class Worker(ExThread):
    """ A class which contains the worker thread logic
    """

    def __init__(self, parent):
        # copy over args from parent to self
        self.args = parent.args

        # copy over any other values from parent to self
        self.irw = parent.irw

        ExThread.__init__(self)

    def collect_results(self, subsessionids):

        print("Collecting results for {} races".format(len(subsessionids)))
        print_progress(0, len(subsessionids), prefix="Progress: ", suffix="of results collected  ")
        event_count = 0
        result_count = 0
        for subsessionid in subsessionids:
            event_count += 1
            good_session = False
            race = EventResult.select().where(EventResult.subsessionid == subsessionid)
            if not race.exists():
                good_session = True
            try:
                event_results = self.irw.event_results(subsessionid)
            except IndexError:
                good_session = False
            if good_session:
                finposs = {}
                results = event_results[1]
                for result in results:
                    if result['carclassid'] not in finposs.keys():
                        finposs[result['carclassid']] = 1
                    else:
                        finposs[result['carclassid']] += 1
                    result_count += 1

                    for laptime_var in ['qualifytime', 'averagelaptime', 'fastestlaptime']:
                        if result[laptime_var] == "00.000":
                            result[laptime_var] = None
                        if result[laptime_var]:
                            if result[laptime_var].find(":") > -1:
                                t = datetime.datetime.strptime(result[laptime_var], "%M:%S.%f")
                                result[laptime_var] = (t.minute * 60) + t.second + (t.microsecond / 1000000)
                            else:
                                result[laptime_var] = float(result[laptime_var])

                    result['subsessionid'] = subsessionid
                    if int(result['custid']) < 0:
                        Team.insert(id=result['teamid'], name=result['name']).on_conflict('REPLACE').execute()
                    else:
                        try:
                            EventResult.insert(**result).on_conflict('IGNORE').execute()
                        except:
                            print(result)
                    
            print_progress(event_count, len(subsessionids), prefix="Progress: ", suffix="of results collected  ")

        print("Race results for {} drivers saved to database".format(result_count))


    def run_with_exception(self):
        thread_name = threading.current_thread().name

        if not self.irw.logged:
            raise MyException("ERROR: {}".format("Login failed. Please check your credentials."))
        else:
            print("Updating service information...")
            print("Updating Cars.")
            cars = []
            for car in self.irw.CARS:
                query = Car.select().where(Car.carid == self.irw.CARS[car]['id'])
                if not query.exists():
                    cars.append({
                        "carid": self.irw.CARS[car]['id'],
                        "abbrevname": self.irw.CARS[car]['abbrevname'],
                        "name": self.irw.CARS[car]['name'],
                        "dirpath": self.irw.CARS[car]['dirpath'],
                    })
            if cars:
                Car.insert_many(cars).execute()

            print("Updating Car Classes.")
            carclasses = []
            for carclass in self.irw.CARCLASS:
                query = CarClass.select().where(CarClass.carclassid == self.irw.CARCLASS[carclass]['id'])
                if not query.exists():
                    carclasses.append({
                        "carclassid": self.irw.CARCLASS[carclass]['id'],
                        "name": self.irw.CARCLASS[carclass]['name'],
                        "shortname": self.irw.CARCLASS[carclass]['shortname'],
                    })
            if carclasses:
                CarClass.insert_many(carclasses).execute()

            print("Updating Tracks.")
            tracks = []
            for track in self.irw.TRACKS:
                query = Track.select().where(Track.trackid == self.irw.TRACKS[track]['id'])
                if not query.exists():
                    tracks.append({
                        "trackid": self.irw.TRACKS[track]['id'],
                        "name": self.irw.TRACKS[track]['name'],
                        "config": self.irw.TRACKS[track]['config'],
                        "lowerNameAndConfig": self.irw.TRACKS[track]['lowerNameAndConfig'],
                        "catid": self.irw.TRACKS[track]['catid'],
                        "freeWithSubscription": self.irw.TRACKS[track]['freeWithSubscription'],
                    })
            if tracks:
                Track.insert_many(tracks).execute()

            print("Updating Series.")
            seasons = []
            self.current_seasons = {}
            self.current_seasonids = []
            self.collected_seasons = {}
            query = Series.select()
            for res in query:
                self.collected_seasons[res.seasonid] = res.seriesname
                if self.args.seasons:
                    print("seasonid {} = {}".format(res.seasonid, res.seriesname))
            if self.args.seasons:    
                return True

            seasons = ['2019-2']

            for season in seasons:
                year, quarter = season.split('-')
                try:
                    r = self.irw.results_archive(race_type=ct.RACE_TYPE_ROAD, event_types=ct.ALL, date_range=ct.ALL, season=(year, quarter, ct.ALL))
                    event_count = r[1]
                    print("Events found: {}".format(event_count))
                    i = 0
                    if event_count > 0:
                        res = r[0]
                        page_count = event_count / 25
                        page_count += 1
                        for event in res:
                            print_progress(i, event_count, prefix="Progress: ", suffix="of events collected  ")
                            Event.insert(**event).on_conflict('IGNORE').execute()
                            i += 1
                        page = 2

                        while page < page_count:
                            r = self.irw.results_archive(race_type=ct.RACE_TYPE_ROAD, event_types=ct.ALL, date_range=ct.ALL, season=(year, quarter, ct.ALL), page=page)
                            res = r[0]
                            for event in res:
                                print_progress(i, event_count, prefix="Progress: ", suffix="of events collected  ")
                                Event.insert(**event).on_conflict('IGNORE').execute()
                                i += 1
                            page += 1

                        events_q = Event.select(Event.subsessionid).distinct()
                        subsessionids = [r.subsessionid for r in events_q]

                        if len(subsessionids) == 0:
                            print("No races found")
                        else:                    
                            self.collect_results(subsessionids)
                except:
                    pass


class App(object):
    """ The main class of your application
    """

    def __init__(self, log, args, cfg):
        self.log = log
        self.args = args
        self.cfg = cfg

        self.irw = iRWebStats(verbose=False)
        print("Logging in...")
        self.irw.login(self.args.username, self.args.password, get_info=True)

        self.log.info("{}: {}".format(__program__, __version__))
        if self.args.debug:
            print("Version {}: {}".format(__program__, __version__))

    def run(self):
        t = Worker(self)
        t.start()
        try:
            t.join_with_exception()
        except MyException as e:
            print("{}".format(e))


def parse_args(argv):
    """ Read in any command line options and return them
    """

    # Define and parse command line arguments
    parser = argparse.ArgumentParser(description=__program__)
    parser.add_argument("-l", "--log", help="file to write log to")
    parser.add_argument("--configfile", help="config file", default="config.ini")
    parser.add_argument("--debug", action='store_true', default=False)
    parser.add_argument("--test", action='store_true', default=False)
    parser.add_argument("-u", "--username", help="your iRacing username (ie: email address you signed up with)", default=None)
    parser.add_argument("-p", "--password", help="your iRacing password (I promise I don't harvest these....)", default=None)
    parser.add_argument('-y', '--year', type=int, default=[], help='the year(s) to collect results for')
    parser.add_argument('-q', '--quarter', type=int, default=[], help='the quarter(s) to collect results for')

    # uncomment this if you want to force at least one command line option
    # if len(sys.argv)==1:
    #    parser.print_help()
    #    sys.exit(1)

    args = parser.parse_args()

    return args

def setup_logging(args):
    """ Everything required when the application is first initialized
    """

    basepath = os.path.abspath(".")

    # set up all the logging stuff
    LOG_FILENAME = os.path.join(basepath, "%s.log" % __program__)

    # If the log file is specified on the command line then override the default
    if args.log:
        LOG_FILENAME = "%s.log" % args.log

    if args.debug:
        LOG_LEVEL = logging.DEBUG
    else:
        LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

    # Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
    # Give the logger a unique name (good practice)
    log = logging.getLogger(__name__)
    # Set the log level to LOG_LEVEL
    log.setLevel(LOG_LEVEL)
    # Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
    handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
    # Format each log message like this
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    # Attach the formatter to the handler
    handler.setFormatter(formatter)
    # Attach the handler to the logger
    log.addHandler(handler)

def main(raw_args):
    """ Main entry point for the script.
    """

    # call function to parse command line arguments
    args = parse_args(raw_args)

    # setup logging
    setup_logging(args)

    # connect to the logger we set up
    log = logging.getLogger(__name__)

    # check if config exists
    if not os.path.isfile(args.configfile):
        config = configobj.ConfigObj()
        config.filename = args.configfile

        config['database_file'] = 'database.sqlite3'
        config['Auth'] = {}
        config['Auth']['username'] = ''
        config['Auth']['password'] = ''
        config['Options'] = {}
        config['Options']['weekly_minimum_count'] = '3'
        config['Options']['season_minimum_week_percent'] = '75'
        config.write()

        # if we need the user to put something in the config uncomment this
        #log.error("Please configure things in the config.ini file")
        #sys.exit(1)

    # try to read in the config
    try:
        cfg = configobj.ConfigObj(args.configfile)
    except (IOError, KeyError, AttributeError) as e:
        log.error("Unable to successfully read config file: %s" % args.configfile)
        sys.exit(1)

    # fire up our base class and get this app cranking!
    app = App(log, args, cfg)

    # things that the app does go here:
    app.run()

    pass

if __name__ == '__main__':
    sys.exit(main(sys.argv))
