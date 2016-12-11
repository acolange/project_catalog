import sys

sys.path.append('/vagrant/catalog/catalog')

from project import app as application
application.secret_key='super_secret_key'
