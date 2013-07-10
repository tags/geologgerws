import os
activate_this = os.path.join(os.getcwd(), 'virtpy/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

import site
site.addsitedir(os.getcwd())

import cherrypy
from siteconf import Root as Root

application = cherrypy.Application(Root(), script_name=None, config=None)


if __name__ == '__main__':
    
    cherrypy.engine.start()
    cherrypy.engine.block()
