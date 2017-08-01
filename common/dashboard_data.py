# -*- coding: utf-8 -*-

import pymongo, ast, json, copy
from datetime import datetime
import MySQLdb, MySQLdb.cursors
from bson.objectid import ObjectId

course = 'course-v1:SNUx+EDU701+2015_11'
client = pymongo.MongoClient('hostname', 27017)
current_db_version = "test"

types = ['play_video', 'pause_video', 'seek_video', 'stop_video', 'page_close', 'xblock.survey.submitted', \
         'edx.forum.thread.created', 'edx.forum.response.created', 'problem_check']

def get_group():
    con = MySQLdb.connect(host="hostname", db='dbname', user='username',passwd='password',charset='utf8',cursorclass=MySQLdb.cursors.DictCursor)
    cur = con.cursor()
    cur.execute("DROP TABLE group_status")
    con.commit()
    sql_create = "create table group_status select name, username from (SELECT name, user_id FROM course_groups_courseusergroup JOIN course_groups_courseusergroup_users ON course_groups_courseusergroup.id=course_groups_courseusergroup_users.courseusergroup_id where course_id='course-v1:SNUx+EDU701+2015_11') as a right join (select username,user_id from student_courseenrollment join auth_user on student_courseenrollment.user_id=auth_user.id where student_courseenrollment.course_id='course-v1:SNUx+EDU701+2015_11' and student_courseenrollment.is_active=1) as b using (user_id)"
    cur.execute(sql_create)
    con.commit()
    sql="SELECT name, GROUP_CONCAT(username) FROM group_status GROUP BY name"
    cur.execute(sql)
    result = list(cur.fetchall())
    con.close()
    group = []
    for i in result:
        temp = {}
	if i['name'] == None:
	    temp['group_name'] = 'Unassigned Group'
    	else:
            temp['group_name'] = i['name']
        temp['group_member'] = i['GROUP_CONCAT(username)'].split(',')
        group.append(temp)
    return group

def get_assets():
    new_assets = []
    mongodb_connection_for_asset(course_id)
    new_assets = get_asset_data(current_db_version)
    return new_assets
 
def mongodb_connection_for_asset(course_id):
    global current_db_version
    a = course_id.split('+')
    client = pymongo.MongoClient('hostname', 27017)
    db = client.edxapp
    version = db.modulestore.active_versions.find({"course":a[1], "run":a[2]}, {"_id":0, "versions":1})
    temp = [l for l in version]
    version_list = temp[0]['versions']
    # print current_db_version
    if version_list['published-branch'] == current_db_version:
        need_to_update_asset = False
    else:
        current_db_version = version_list['published-branch']
        need_to_update_asset = True
    return current_db_version, need_to_update_asset

def get_asset_data(current_db_version):
    client = pymongo.MongoClient('hostname', 27017)
    db = client.edxapp
    structure = db.modulestore.structures
    module_structure = structure.find({"_id": current_db_version},{"_id":0, "blocks":1})
    temp = [l for l in module_structure]
    module_structure_list = temp[0]['blocks']
    # contents_blocks
    assets = []
    asset_sequential = []
    asset_vertical = []
    asset_chapter = []
    i=0
    for mdl_str in module_structure_list:
        temp_video ={}
        temp_problem = {}
        temp_discussion = {}
        temp_sga = {}
        temp_html = {}
        if mdl_str['block_type'] == 'video':
            temp_video['block_id'] = mdl_str['block_id']
            temp_video['block_type'] = mdl_str['block_type']
            try:
                temp_video['display_name'] = mdl_str['fields']['display_name']
                temp_video['start_time'] = mdl_str['fields']['start_time']
                temp_video['end_time'] = mdl_str['fields']['end_time']
            except KeyError:
                temp_video['display_name'] = None
                temp_video['start_time'] = None
                temp_video['end_time'] = None
            assets.append(temp_video)
        elif mdl_str['block_type'] == 'problem':
            temp_problem['block_id'] = mdl_str['block_id']
            temp_problem['block_type'] = mdl_str['block_type']
            try:
                temp_problem['display_name'] = mdl_str['fields']['display_name']
            except KeyError:
                temp_problem['display_name'] = None
            temp_problem['start_time'] = None
            temp_problem['end_time'] = None
            assets.append(temp_problem)
        elif mdl_str['block_type'] == 'discussion':
            temp_discussion['block_id'] = mdl_str['block_id']
            temp_discussion['block_type'] = mdl_str['block_type']
            temp_discussion['display_name'] = None
            temp_discussion['start_time'] = None
            temp_discussion['end_time'] = None
            assets.append(temp_discussion)
        elif mdl_str['block_type'] == 'edx_sga':
            temp_sga['block_id'] = mdl_str['block_id']
            temp_sga['block_type'] = mdl_str['block_type']
            temp_sga['display_name'] = None
            temp_sga['start_time'] = None
            temp_sga['end_time'] = None
            assets.append(temp_sga)
        elif mdl_str['block_type'] == 'html':
            temp_html['block_id'] = mdl_str['block_id']
            temp_html['block_type'] = mdl_str['block_type']
            try:
                temp_html['display_name'] = mdl_str['fields']['display_name']
            except KeyError:
                temp_html['display_name'] = None
            temp_html['start_time'] = None
            temp_html['end_time'] = None
            assets.append(temp_html)
        elif mdl_str['block_type'] == 'sequential':
            asset_sequential.append(mdl_str)
        elif mdl_str['block_type'] == 'vertical':
            asset_vertical.append(mdl_str)
        elif mdl_str['block_type'] == 'chapter':
            asset_chapter.append(mdl_str)
        i+=1
    new_assets = []
    
    for asset in assets:
        block_id = asset['block_id']
        for vertical in asset_vertical:
            for child in vertical['fields']['children']:
                if block_id == child[1]:
                    v_block_id = vertical['block_id']
                    asset['v_block_id'] = v_block_id
        try:
            a = asset['v_block_id']
            for sequential in asset_sequential:
                for child in sequential['fields']['children']:
                    if v_block_id == child[1]:
                        s_block_id = sequential['block_id']
                        asset['s_block_id'] = s_block_id
            for chapter in asset_chapter:
                for child in chapter['fields']['children']:
                    if s_block_id == child[1]:
                        c_block_id = chapter['block_id']
                        asset['week_name'] = chapter['fields']['display_name']
                        asset['c_block_id'] = c_block_id
            new_assets.append(asset)
        except KeyError:
            continue
    con = None
    con = MySQLdb.connect(host='hostname',db='dbname', user='username',passwd='password', charset='utf8',cursorclass=MySQLdb.cursors.DictCursor)
    cur = con.cursor()
    cur.execute("DELETE FROM course_assets")
    con.commit()
    sql = """INSERT INTO course_assets (block_type,block_id,v_block_id,s_block_id, c_block_id,week_name,display_name,start_time,end_time) VALUES (%(block_type)s, %(block_id)s, %(v_block_id)s, %(s_block_id)s, %(c_block_id)s, %(week_name)s, %(display_name)s, %(start_time)s, %(end_time)s)"""
    cur.executemany(sql, new_assets)
    con.commit()
    con.close()
    return new_assets

def get_total_log():
    client = pymongo.MongoClient('hostname', 27017)
    data = client.data.tracking_logs
    result = data.aggregate([
	    {"$match": {"time":{"$gte":'2015-11-02T00:00:00.000000'},
			"course_id": course,
			"event_type":{"$in":types}
			}},
            {"$project" :
                        {
                            "username" : 1,
                            "time": 1,
                            "_id" : 0,
                            "event" : 1,
                            "event_type" :1,
                            "event_source" : 1
                        }}
            ])

    log = [] 
    for r in result['result']:
        log.append(r)
    result = data.aggregate([
            {"$match" :
                        {  
                            "course_id" : course,
                            "event_type" : {"$regex":'upload_assignment', "$options":'^'},
                            "event_source" : "server"
                        }},
            {"$project" :
                        {
                            "username" : 1,
                            "time": 1,
                            "_id" : 0,
                            "event" : 1,
                            "event_type" :1,
                            "event_source" : 1
                        }}
            ])
    for r in result['result']:
        log.append(r)
    return log


def get_user_log(log,name):
    blog = []  
    slog = []   
    for i in log:
        if i['username'] == name:
            if i['event_source'] == 'browser':
                blog.append(i)
            elif i['event_source'] == 'server':
                slog.append(i)
    return blog, slog

def get_video(blog):    
    a = {}  
    for n in range(len(blog)-1):
        i = blog[n]
        j = blog[n+1]        
        if i['event_type'] == 'play_video':
            b = i['event']
            b = ast.literal_eval(b)
            video_id = b['id']
            d = 0
            if (n != 0) and (blog[n-1]['event_type'] == 'seek_video'):
                b['currentTime'] = ast.literal_eval(blog[n-1]['event'])['new_time']
            if video_id not in a.keys():
                a[video_id] = {'sum': 0 , 'time' : ''}
            if j['event_type'] == 'pause_video':
                c = j['event']
                c = ast.literal_eval(c)
                d = c['currentTime'] - b['currentTime']
            if j['event_type'] == 'seek_video':
                c = j['event']
                c = ast.literal_eval(c)
                d = c['old_time'] - b['currentTime']
            if j['event_type'] == 'stop_video':
                c = j['event']
                c = ast.literal_eval(c)
                d = c['currentTime'] - b['currentTime']
            if j['event_type'] == 'page_close':
                s = i['time'][11:19]
                s = datetime.strptime(s, "%H:%M:%S")
                e = j['time'][11:19]
                e = datetime.strptime(e, "%H:%M:%S")
                d = e-s
                d = d.seconds
            if d > 0:
                a[video_id]['sum'] += d
    video = []
    for i in a.keys():
        j = {'block_id' : i, 'sum' : a[i]['sum']}
        video.append(j)
    return video

def get_problem(slog):
    a ={}
    for i in slog:
        if i['event_type'] == "problem_check":
            answer = {}
            block_id = i['event']["problem_id"][-32:]
            j = i['event']['submission'].values()
            for k in j:
                if k['response_type'] == 'multiplechoiceresponse':
                    answer['choice'] = k['answer']
                elif k['response_type'] == 'customresponse':
                    answer['reason'] = k['answer']
                else: continue
            if block_id not in a.keys():
                a[block_id] = {'time' : '', 'status': True, 'answer': answer}
            else: 
                a[block_id]['answer'] = answer
    problem = []
    for i in a.keys():
        j = {'block_id' : i, 'status' : a[i]['status'], 'answer' : a[i]['answer']}
        problem.append(j)
    return problem

def get_discussion(slog):
    commentable = {'1': [], '2':[], '3':[]}
    forum = []
    for i in slog: 
        if (i['event_type'] == 'edx.forum.thread.created')  \
        or (i['event_type'] == 'edx.forum.response.created'):
            forum.append(i)
    for j in forum:
        week_number = j['event']['category_name'][0]
        try: 
            commentable[week_number].append(j['event']['id'])
	    commentable[week_number] = map((lambda x: ObjectId(x)), commentable[week_number])
        except KeyError: pass
    #print commentable
    discussion = {'1' : [], '2':[], '3':[]}
    if len(forum) > 0: 
        writer = forum[0]['username']
        for w in discussion.keys():
            client = pymongo.MongoClient('localhost', 27017)
            db_forum = client.cs_comments_service_development
            content = db_forum.contents
            result = content.aggregate([
            {"$match": {
                "author_username": writer,
                "course_id": course,
                "_id": {"$in":commentable[w]}
            }},
            {"$project": {
                "_id": 0,
                "thread_type": 1,
                "votes.up_count":1
            }},
            {"$group": {
                "_id": {"type": "$thread_type"},
                "total": {"$sum": 1},
                "vote_total":{"$sum":"$votes.up_count"}
            }},
            {"$project": {
                "_id": 0,
                "type": "$_id.type",
                "total": "$total",
                "vote_total":"$vote_total"}
            }])
            discussion[w] = result['result']
    return discussion


def get_assignment(slog):
    a = {}
    for i in slog:
        if 'assignment' in i['event_type']:
            block_id = i['event_type'].split('@')[2][:32]
            if block_id not in a.keys():
                a[block_id] = {'time' : '', 'status': True}
    assignment = []
    for i in a.keys():
        j = {'block_id' : i, 'status' : a[i]['status']}
        assignment.append(j)
    return assignment

def get_survey(slog):
    a = {}
    for i in slog:
        if i['event_type'] == 'xblock.survey.submitted':
            block_id = i['event']['url_name']
            if block_id not in a.keys():
                a[block_id] = {'time' : '', 'status': True, 'answer': ''}
    survey = []
    for i in a.keys():
        j = {'block_id' : i, 'status' : a[i]['status']}
        survey.append(j)
    return survey

def get_dashboard():
    con = None
    con = MySQLdb.connect(host="hostname",db='dbname', user='username',passwd='password',charset='utf8',cursorclass=MySQLdb.cursors.DictCursor)
    cur = con.cursor()
    cur.execute("select * from course_assets")
    asset = list(cur.fetchall())
    con.close()
    
    log = get_total_log()
    student = []
    group = get_group()

    for g in group:
	student += g['group_member']

    board = []
    b = {    'week_1' :{                 \
                'goal'      : {},        \
                'video'     : [],        \
                'think'     : [],        \
                'i_solution': {},        \
                'g_solution': {},        \
                'reflection': [],        \
                'discussion': [],        \
                'progress'  : 0          \
                },                       \
             'week_2' :{                 \
                'goal'      : {},        \
                'video'     : [],        \
                'think'     : [],        \
                'i_solution': {},        \
                'g_solution': {},        \
                'reflection': [],        \
                'discussion': [],        \
                'progress'  : 0,         \
                },                       \
             'week_3' :{                 \
                'goal'      : {},        \
                'video'     : [],        \
                'think'     : [],        \
                'i_solution': {},        \
                'g_solution': {},        \
                'reflection': [],        \
                'discussion': [],        \
                'progress'  : 0          \
                }
            }
    for a in asset:
        block_id = a["block_id"]
        block_type = a["block_type"]
        display_name = a["display_name"]
        if block_type == 'video': 
            start_time = datetime.strptime(str(a['start_time']), "%H:%M:%S")
            end_time = datetime.strptime(str(a['end_time']), "%H:%M:%S")
            total_time = (end_time - start_time).seconds
            watch_time = 0 
            status = 0
            position = 'v' + display_name[0] 
            b['week_' + a["week_name"][0]]['video'].append({ 'block_id': block_id, 'total_time': total_time, 'watch_time':watch_time, 'status':  status, 'display_name':display_name, 'position' : position})
        if block_type == 'problem':
            status = False
            if u'\uc0dd\uac01' in display_name:
                category = 'think'
                position = 't' + display_name[-1]
                answer = {}
                b['week_' + a["week_name"][0]][category].append({ 'block_id': block_id, 'status': status, 'display_name':display_name, 'position': position, 'answer': answer})
            else:
                if u'\ubaa9\ud45c' in display_name:
                    category = 'goal'
                    b['week_' + a["week_name"][0]][category]['block_id'] = block_id
                    b['week_' + a["week_name"][0]][category]['status'] = status
                    b['week_' + a["week_name"][0]][category]['display_name'] = display_name
                elif a['section_name'] == u'\uc131\ucc30':
                    category = 'reflection'
                    b['week_' + a["week_name"][0]][category].append({ 'block_id': block_id, 'status': status, 'display_name':display_name, 'position' : 'r2'})
        if block_type == 'survey':
            b['week_' + a["week_name"][0]]['reflection'].append({ 'block_id': block_id, 'status': status, 'display_name':display_name, 'position' : 'r1'})
        if block_type == 'edx_sga':
            status = False
            category = ""
            section = a['section_name']
            if u"\uac1c\uc778" in section:
                category = 'i_solution'
            elif u"\uadf8\ub8f9" in section:
                category = 'g_solution'
            b['week_' + a["week_name"][0]][category]['block_id'] =  block_id
            b['week_' + a["week_name"][0]][category]['status'] = status
    for name in student:
        c = copy.deepcopy(b)
        c['name'] = name
        c['group'] = "unassigned"
        for g in group:
            if name in g['group_member']:
                c['group'] = g['group_name']
        blog, slog = get_user_log(log,name)
        discussion  = get_discussion(slog)
        c['week_1']['discussion'] = discussion['1']
        c['week_2']['discussion'] = discussion['2']
        c['week_3']['discussion'] = discussion['3']        
        video = get_video(blog)
        for v in video:
            block_id = v['block_id']
            for a in asset:
                if a['block_id'] == block_id:
                    w = 'week_' + a["week_name"][0]
                    for z in c[w]['video']:
                        if z['block_id'] == block_id:
                            total_time = z['total_time']
                            watch_time = v['sum']
                            ratio = float( watch_time )/ total_time
                            status = z['status']
                            if ratio >= 0.7: 
                                status = 2
                                c[w]['progress'] += 1
                                if ratio >= 1:
                                    watch_time = total_time
                            elif ratio > 0:
                                c[w]['progress'] += 0.5
                                status = 1
                            if status != 0:
                                z['watch_time'] = watch_time
                                z['status'] = status
        problem = get_problem(slog)
        for p in problem:
            block_id = p['block_id']
            for a in asset:
                if a['block_id'] == block_id:
                    w = 'week_' + a["week_name"][0]
                    display_name = a["display_name"]
                    if u'\uc0dd\uac01' in display_name:
                        for z in c[w]['think']:
                            if z['block_id'] == block_id:
                                z['answer'] = p['answer']
                                z['status'] = p['status']
                                c[w]['progress'] += 0.5
                    elif u'\ubaa9\ud45c' in display_name:
			c[w]['goal']['answer'] = p['answer']
                        c[w]['goal']['status'] = p['status']
                        c[w]['progress'] += 1
                    elif a['section_name'] == u'\uc131\ucc30':
                        for z in c[w]['reflection']:
                            if z['block_id'] == block_id:
				z['answer'] = p['answer']
                                z['status'] = p['status']
                                c[w]['progress'] += 1                       
        survey = get_survey(slog)
        for u in survey:
            block_id = u['block_id']
            for a in asset:
                if a['block_id'] == block_id:
                    w = 'week_' + a["week_name"][0]
                    for z in c[w]['reflection']:
                        if z['block_id'] == block_id:
                            z['status'] = u['status']
                            c[w]['progress'] += 1
        assignment = get_assignment(slog)
        for s in assignment:
            block_id = s['block_id']
            for a in asset:
                if a['block_id'] == block_id:
                    w = 'week_' + a["week_name"][0]
                    section = a["section_name"]
                    if u"\uac1c\uc778" in section:
                        c[w]['i_solution']['status'] = s['status'] 
                        c[w]['progress'] += 2      
                    elif u"\uadf8\ub8f9" in section:
                        c[w]['g_solution']['status'] = s['status']    
        board.append(c)
    for w in ['1','2','3']: 
        for g in group:
            g_submission = False
            for m in g['group_member']:
                for c in board:
                    if c['name'] == m:
                        if c['week_' + w]['g_solution']['status'] == True:
                                g_submission = True
            for m in g['group_member']:
                for c in board:
                    if c['name'] == m:
                        c['week_' + w]['g_solution']['status'] = g_submission
                        if c['week_' + w]['g_solution']['status'] == True:
                            c['week_' + w]['progress'] += 2
    for c in board:
        total_progress = 0
        for w in ['1','2','3']:   
            week = c['week_' + w]
            progress = week['progress']
            total_progress += progress
        c['total_progress'] = float(total_progress) / 30

    del log,blog,slog 
    return board