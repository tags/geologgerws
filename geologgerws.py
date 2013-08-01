################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2013 The University of Oklahoma
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.                                   
################################################################################
#
# A web service to get data stored in mongodb for the geologger web application.
# 
# Jonah Duckles - jduckles@ou.edu
# 

'''
GET /lightlogs - list of available lightlog tagnames
GET /lightlogs/tagname - a single tagname's most recent lightlog
GET /twilights/ - a list of available twilight tagnames
GET /twilights/tagname - a single tagnamees' most recent twilight data
GET /coord/ - a list of available geospatial coordinates and their timestamp
GET /coord/tagname - a single tagnames' most recent coordinate data
'''


import cherrypy
import pymongo
import psycopg2
import json
from json_handler import handler

import logging
logging.basicConfig(level=logging.INFO)

def distinct(seq):
    ''' returns distinct elements of a sequence '''
    seen=set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x) ]


class Root(object):
    
    def __init__(self):
        ''' Intialize database connections '''
        self.db = pymongo.Connection()
        self.auth = psycopg2.connect(dbname="auth", user='mstacy', host="fire.rccc.ou.edu")
    def uidtoname(self,user_id):
        ''' Convert uid to username ''' 
        cur = self.auth.cursor()
        if user_id:
            cur.execute('select username from auth_user where id = %s' % user_id)
            return cur.fetchone()[0]
        else:
            return 'guest'
    def geologgercollection(self,collection,username,querytype,queryid=None):
        '''Get data from MongDB based on client's username'''
        try:
            col = self.db['geologger'][collection]
        except:
            logging.exception("Collection not found, either it doesnt exist or can't connect to Mongo")
        if collection == "coord":
            tagnamekey = 'properties.tagname'
            useridkey = 'properties.user_id'
            timestampkey = 'properties.timestamp'
            if querytype == "id":
                query = col.find(spec = {useridkey: username, "_id": queryid}, 
                sort= [[timestampkey, -1]], limit=1, fields={'_id':False})
            elif querytype == "tagname":
                query = col.find(spec = {useridkey: username,  tagnamekey: queryid}, 
                sort = [[timestampkey, -1]], limit =1, fields={'_id':False} )
        else:
            tagnamekey = 'tagname'
            useridkey = 'user_id'
            timestampkey = 'timestamp'
            if querytype == "id":
                query = col.find(spec = {useridkey: username, "_id": queryid}, 
                sort= [[timestampkey, -1]], limit=1, fields={'_id':False})
            elif querytype == "tagname":
                query = col.find(spec={useridkey: username, tagnamekey: queryid}, 
                sort = [['timestamp', -1]], limit = 1, fields={'_id': False}) 
        if queryid:
            record = [ item for item in query]
            if len(record) > 0:
                return json.dumps(record, default=handler, indent=2)
            else:
                return "{error: Nothing found with that tagname}"
        else:
            tags = col.distinct(tagnamekey)
            tagsout = list()
            for tag in tags:
                query = col.find(spec={useridkey: username, tagnamekey: tag }, sort = [['timestamp', -1]], limit=1, fields={'_id': False, tagnamekey: True, timestampkey:True})
                if query.count() > 0:
                    tagsout.append([item for item in query ][0])
            return json.dumps(tagsout, default=handler, indent=2)
    @cherrypy.expose    
    def index(self):
        return '''<html><ul><li><a href="lightlogs">lightlogs</a></li><li>
                <a href="twilights">twilights</a></li><li><a href="coord">coord</a></li></ul></html>
               ''' 
    @cherrypy.expose    
    def lightlogs(self,querytype,queryid=None,callback=None, **kwargs):
        user_id = cherrypy.request.login
        if user_id != 'guest':
            username = self.uidtoname(user_id)
        else:
            username = 'guest'
        
        out = self.geologgercollection('lightlogs',username,querytype,queryid)
        if callback:
            cherrypy.response.headers['Content-Type'] = "application/javascript"
            return '%s(%s)'.encode('utf-8') % (str(callback),out)
        else:
            cherrypy.response.headers['Content-Type'] = "application/json"
            return out
    @cherrypy.expose
    def twilights(self,querytype,queryid=None,callback=None, **kwargs):
        user_id = cherrypy.request.login
        if user_id != 'guest':
            username = self.uidtoname(user_id)
        else:
            username = 'guest'
        out = self.geologgercollection('twilights',username,querytype,queryid, **kwargs)
        if callback:
            cherrypy.response.headers['Content-Type'] = "application/javascript"
            return u'%s(%s)' % (str(callback),out)
        else:
            cherrypy.response.headers['Content-Type'] = "application/json"
            return out
    @cherrypy.expose
    def coord(self, querytype, queryid=None,callback=None, **kwargs):
        user_id = cherrypy.request.login
        if user_id != 'guest':
            username = self.uidtoname(user_id)
        else:
            username = 'guest'
        out = self.geologgercollection('coord',username,querytype,queryid, **kwargs)
        if callback:
            cherrypy.response.headers['Content-Type'] = "application/javascript"
            return u'%s(%s)' % (str(callback),out)
        else:
            cherrypy.response.headers['Content-Type'] = "application/json"
            return out
    


cherrypy.tree.mount(Root())
application = cherrypy.tree

if __name__ == '__main__':
    cherrypy.engine.start()
    cherrypy.engine.block()
