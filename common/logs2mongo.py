'''
This script loads tracking logs to mongodb
Tracking logs are generated daily
we will load all logs to a master tracking_logs collection within our master database
From the master tracking logs collection we extract course specific tracking logs
Course specific tracking logs are loaded to a course specific database in collection called tracking

Note, this script works with both decompressed (.log) and compressed (.log.gz) tracking logs

Usage: python load_tracking_logs_to_mongo.py <database_name> <collection_name> <path_to_directory_containing_trackings_logs>
Note, use tracking as both the database_name and the collection_name

*Some errors occur when loading open assessments events

'''

import pymongo
import sys
import json
import gzip
import datetime
import os
from collections import defaultdict
from dateutil.parser import parse

ERROR_FILE_SUFFIX = "-errors"


def connect_to_db_collection(db, collection):
    db_name = db
    collection_name = collection
    
    # Get database connection and collections
    connection = pymongo.Connection('hostname', 27017)
    db = connection[db_name]
    tracking = db[collection_name]
    tracking_imported = db[collection_name + "_imported"]
    return tracking, tracking_imported

def get_course_id(event):
    """
    Try to harvest course_id from various parts of an event.  Assumes that
    the "event" has already been parsed into a structure, not a json string.
    The course_id should be of the format A/B/C and cannot contain dots.
    """
    course_id = None
    if event['event_source'] == 'server':
        # get course_id from event type
        if event['event_type'] == '/accounts/login/':
            s = event['event']['GET']['next'][0]
        else:
            s = event['event_type']
    else:
        s = event['page']
    if s:
        a = s.split('/')
        if 'courses' in a:
            i = a.index('courses')
            if (len(a) >= i+4):
                course_id = "/".join(a[i+1:i+4]).encode('utf-8').replace('.','')
    return course_id

def get_log_file_name(file_path):
    """
    Save only the filename and the subdirectory it is in, strip off all prior
    paths.  If the file ends in .gz, remove that too.  Convert to lower case.
    """
    file_name = '/'.join(file_path.lower().split('/')[-1:])
    if len(file_name) > 3 and file_name[-3:] == ".gz":
        file_name = file_name[:-3]
    return file_name


def get_tracking_logs(path_to_logs):
    '''
    Retrieve all logs files from command line whether they were passed directly
    as files or directory

    '''
    logs = []
    for path in path_to_logs: 
        if os.path.isfile(path):
            logs.append(path)
        elif os.path.isdir(path):
            for (dir_path, dir_names, file_names) in os.walk(path):
                for name in file_names:
                    logs.append(os.path.join(dir_path, name))
    return logs


def load_log_content(log):
    '''
    Return log content 

    '''
    if log.endswith('.gz'):
        file_handler = gzip.open(log)
        log_content = file_handler.readlines()
        file_handler.close()
    else:
        with open(log) as file_handler:
            log_content = file_handler.readlines()
    return log_content


def migrate_tracking_logs_to_mongo(tracking, tracking_imported, log_content, log_file_name):
    '''
    Migrate tracking logs to the tracking collection in the database

    '''
    errors = []
    log_to_be_imported = {}
    log_to_be_imported['_id'] = log_file_name
    log_to_be_imported['date'] = datetime.datetime.utcnow()
    log_to_be_imported['error'] = 0
    log_to_be_imported['success'] = 0
    log_to_be_imported['courses'] = defaultdict(int)
    
    duplicated_count = 0
    after = log_to_be_imported['date']

    lastTime = tracking.aggregate([{"$sort":{"time":-1}},{"$project":{"_id":0,"time":1}},{"$limit":1}])['result'][0]['time']
    lastTime = parse(str(lastTime))
    lastTime = datetime.datetime.strftime(lastTime, "%Y-%m-%dT%H:%M:%S.%f")
#    print lastTime
    
# find the time of the last log
# get time diff between current and last log's time

    for record in log_content:
        try:
            data = json.loads(record)
        except ValueError:
            log_to_be_imported['error'] += 1
            errors.append("JSON LOAD: " + record)
            continue
        if data['time'] > lastTime:
            if len(tracking.aggregate([
                 {'$match':
                     {'$and': 
                         [{'time':{'$gte':lastTime}},
                          {'time':data['time']}]}}])['result']) != 0:
                duplicated_count += 1
                continue
            else:
                try:
                    log_to_be_imported['courses'][data['context']['course_id']] += 1
                    data['course_id'] = data['context']['course_id']
                except:
                    course_id = get_course_id(data)
                    if course_id:
                        log_to_be_imported['courses'][course_id] += 1
                        data['course_id'] = course_id
                data['load_date'] = datetime.datetime.utcnow()
                data['load_file'] = log_file_name
                try:
                    tracking.insert(data)
                except pymongo.errors.InvalidDocument as e:
                    errors.append("INVALID_DOC: " + str(data))
                    log_to_be_imported['error'] += 1
                    continue
                except Exception as e:
                    errors.append("ERROR: " + str(data))
                    log_to_be_imported['error'] += 1
                    continue
                log_to_be_imported['success'] += 1
    try:
        tracking_imported.insert(log_to_be_imported)
    except Exception as e:
        errors.append("Error inserting into tracking_imported: " + str(log_to_be_imported))
    return duplicated_count, errors, log_to_be_imported['error'], log_to_be_imported['success']
            

def logs2mongo():
    db = "dbname"
    coll = "collectionname"
    log_path = ['/edx/var/log/tracking/']

    tracking, tracking_imported = connect_to_db_collection(db, coll)
    total_success = 0
    total_errors = 0
    log_files = get_tracking_logs(log_path) 
    for log in sorted(log_files):
        if not log.endswith(ERROR_FILE_SUFFIX):
            log_file_name = get_log_file_name(log)
            if log_file_name != 'tracking.log':
                if tracking_imported.find_one({'_id' : log_file_name}): 
                    continue
                else:
                    log_content = load_log_content(log)
                    error_file_name = log + ERROR_FILE_SUFFIX
                    duplicated_count, errors, error_count, success_count = migrate_tracking_logs_to_mongo(tracking, tracking_imported, log_content, log_file_name)
                    total_success += success_count
                    total_errors += error_count
            else: 
                log_content = load_log_content(log)
                error_file_name = log + ERROR_FILE_SUFFIX
                duplicated_count, errors, error_count, success_count = migrate_tracking_logs_to_mongo(tracking, tracking_imported, log_content, log_file_name)
                total_success += success_count
                total_errors += error_count

    print "Total: ", (total_success + total_errors)
    print "Inserted: ", total_success
    print "Not loaded: ", total_errors
    print "duplicated ", duplicated_count


