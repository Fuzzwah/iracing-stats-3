#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from peewee import *

db_file = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "159155.sqlite3")
db = SqliteDatabase(db_file)


class BaseModel(Model):
    class Meta:
        database = db


class SeriesResult(BaseModel):
    seasonid = IntegerField()
    week_num = IntegerField()
    start_time = IntegerField()
    carclassid = IntegerField()
    trackid = IntegerField()
    sessionid = IntegerField()
    subsessionid = IntegerField()
    officialsession = IntegerField()
    sizeoffield = IntegerField()
    strengthoffield = IntegerField()


    class Meta:
        order_by = ('starttime',)
        db_table = 'series_result'
        primary_key = CompositeKey("subsessionid", "carclassid")


class Team(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()

    class Meta:
        order_by = ('id',)
        db_table = 'teams'


class Event(BaseModel):
    subsessionid = IntegerField()
    sessionid = IntegerField()
    evttype = IntegerField()
    seasonid = IntegerField()
    seriesid = IntegerField()
    season_year = IntegerField()
    season_quarter = IntegerField()
    officialsession = IntegerField()
    race_week_num = IntegerField()
    start_date = CharField()
    start_time = CharField()
    raw_start_time = IntegerField()
    finishedat = IntegerField()
    strengthoffield = IntegerField()
    custid = IntegerField()
    displayname = CharField()
    carclassid = IntegerField()
    carid = IntegerField()
    trackid = IntegerField()
    catid = IntegerField()
    starting_position = IntegerField()
    finishing_position = IntegerField()
    incidents = IntegerField()
    bestquallaptime = CharField()
    bestlaptime = CharField()
    champpoints = IntegerField()
    clubpointssort = IntegerField()
    helm_licenselevel = IntegerField()
    helm_pattern = IntegerField()
    helm_color1 = CharField()
    helm_color2 = CharField()
    helm_color3 = CharField()
    rn = IntegerField()
    sesrank = IntegerField()
    licensegroup = IntegerField()
    clubpoints = IntegerField()
    dropracepoints = IntegerField()
    groupname = CharField()
    winnerdisplayname = CharField()
    winnerlicenselevel = IntegerField()
    winnerhelmpattern = IntegerField()
    winnerhelmcolor1 = CharField()
    winnerhelmcolor2 = CharField()
    winnerhelmcolor3 = CharField()
    winnersgroupid = IntegerField()
    subsession_bestlaptime = CharField()
    champpointssort = IntegerField()

    class Meta:
        order_by = ('subsessionid',)
        db_table = 'events'

class EventResult(BaseModel):
    subsessionid = IntegerField()
    finpos = IntegerField()
    carid = IntegerField()
    car = IntegerField()
    carclassid = IntegerField()
    carclass = CharField()
    teamid = IntegerField()
    custid = IntegerField()
    name = CharField()
    startpos = IntegerField()
    outid = IntegerField()
    out = CharField()
    interval = CharField(null = True)
    lapsled = IntegerField()
    qualifytime = FloatField(null = True)
    averagelaptime = FloatField(null = True)
    fastestlaptime = FloatField(null = True)
    fastlap = IntegerField(null = True)
    lapscomp = IntegerField()
    inc = IntegerField()
    pts = IntegerField()
    clubpts = IntegerField()
    div = CharField()
    clubid = IntegerField()
    club = CharField()
    oldirating = IntegerField(null = True)
    newirating = IntegerField(null = True)
    oldlicenselevel = IntegerField(null = True)
    oldlicensesublevel = IntegerField(null = True)
    newlicenselevel = IntegerField(null = True)
    newlicensesublevel = IntegerField(null = True)
    seriesname = CharField()
    maxfuelfill = IntegerField()
    weightpenaltykg = IntegerField()
    aggpts = IntegerField()


    class Meta:
        order_by = ('sessionid', 'FinPos')
        db_table = 'event_result'
        primary_key = CompositeKey("subsessionid", "custid")


class Car(BaseModel):
    carid = IntegerField(primary_key=True)
    abbrevname = CharField()
    name = CharField()
    dirpath = CharField()


    class Meta:
        order_by = ('carid',)
        db_table = 'cars'


class CarClass(BaseModel):
    carclassid = IntegerField(primary_key=True)
    name = CharField()
    shortname = CharField()


    class Meta:
        order_by = ('carclassid',)
        db_table = 'carclasses'


class Track(BaseModel):
    trackid = IntegerField(primary_key=True)
    name = CharField()
    config = CharField()
    lowerNameAndConfig = CharField()
    catid = IntegerField()
    freeWithSubscription = CharField()


    class Meta:
        order_by = ('trackid',)
        db_table = 'tracks'


class Series(BaseModel):
    seasonid = IntegerField(primary_key=True)
    seriesid = IntegerField()
    catid = IntegerField()
    seriesname = CharField()
    seriesshortname = CharField()
    multiclass = CharField()
    year = IntegerField()
    quarter = IntegerField()
    image = CharField()


    class Meta:
        order_by = ('seasonid',)
        db_table = 'series'


db.connect()

if not SeriesResult.table_exists():
    db.create_tables([SeriesResult,], safe=True)
if not Team.table_exists():
    db.create_tables([Team,], safe=True)
if not Event.table_exists():
    db.create_tables([Event,], safe=True)
if not EventResult.table_exists():
    db.create_tables([EventResult,], safe=True)
if not Car.table_exists():
    db.create_tables([Car,], safe=True)
if not CarClass.table_exists():
    db.create_tables([CarClass,], safe=True)
if not Track.table_exists():
    db.create_tables([Track,], safe=True)
if not Series.table_exists():
    db.create_tables([Series,], safe=True)
