import os
activate_this = '/var/www/apps/geologgerws/' + 'virtpy/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import site
site.addsitedir('/var/www/apps/geologgerws/')

import cherrypy
from siteconf import Root as Root

application = cherrypy.Application(Root(), script_name=None, config=None)


if __name__ == '__main__':
    
    cherrypy.engine.start()
    cherrypy.engine.block()
