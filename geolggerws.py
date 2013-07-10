import cherrypy
import pymongo
import psycopg2
import json
from json_handler import handler

import logging
logging.basicConfig(level=logging.INFO)

def distinct(seq):
    seen=set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x) ]
class Root(object):
    
    def __init__(self):
        self.db = pymongo.Connection()
        self.auth = psycopg2.connect(dbname="auth", user='mstacy', host="fire.rccc.ou.edu")
    def uidtoname(self,user_id):
        cur = self.auth.cursor()
        if user_id:
            cur.execute('select username from auth_user where id = %s' % user_id)
            return cur.findone()
        else:
            return 'guest'
    def geologgercollection(self,collection,username,tagname=None):
        try:
            col = self.db['geologger'][collection]
        except:
            logging.exception("Collection not found, either it doesnt exist or can't connect to Mongo")
        if collection == "coord":
            tagnamekey = 'properties.tagname'
            useridkey = 'properties.user_id'
            query = col.find(spec = {useridkey: username,  tagnamekey: tagname}, sort = [['properties.timestamp', -1]], limit =1, fields={  '_id':False} )
        else:
            tagnamekey = 'tagname'
            useridkey = 'user_id'
            query = col.find(spec={useridkey: username,  tagnamekey:tagname}, sort = [['timestamp', -1]], limit = 1, fields={'_id': False}) 
        if tagname:
            record = [ item for item in query]
            if len(record) > 0:
                return json.dumps(record, default=handler, indent=2)
            else:
                return "{error: Nothing found with that tagname}"
        else:
            tags = [ item for item in col.find(spec={useridkey: username}, fields={tagnamekey:True, '_id':False}) ]
            return json.dumps(tags, default=handler, indent=2)

    @cherrypy.expose
    def test_auth(self):
        if cherrypy.request.headers.has_key('REMOTE_USER'):
            return "Your username is %s" % cherrypy.request.headers['REMOTE_USER']
        else:
            return "There doesn't seem to be an auth system running on your server" 
    @cherrypy.expose    
    def index(self):
        pass 
    @cherrypy.expose    
    def lightlogs(self,tagname=None):
        user_id = cherrypy.request.login
        if user_id != 'guest':
            username = self.uidtoname(user_id)
        cherrypy.response.headers['Content-Type'] = "application/json"
        return self.geologgercollection('lightlogs',username,tagname)
    @cherrypy.expose
    def twilights(self,tagname=None):
        user_id = cherrypy.request.login
        if user_id != 'guest':
            username = self.uidtoname(user_id)
        cherrypy.response.headers['Content-Type'] = "application/json"
        return self.geologgercollection('twilights',username,tagname) 
    @cherrypy.expose
    def coord(self, tagname=None, task_id=None):
        user_id = cherrypy.request.login
        if user_id != 'guest':
            username = self.uidtoname(user_id)
        cherrypy.response.headers['Content-Type'] = "application/json"
        return self.geologgercollection('coord',username, tagname)

cherrypy.tree.mount(Root())
application = cherrypy.tree

if __name__ == '__main__':
    cherrypy.engine.start()
    cherrypy.engine.block()
