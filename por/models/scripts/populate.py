import os
import sys
import transaction
import base64

from sqlalchemy import engine_from_config
from pyramid.paster import get_appsettings, setup_logging

from por.models.dbsession import DBSession
from por.models import Base
from por.models.scripts import add_user, add_role
from por.models.dashboard import GlobalConfig


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, name='dashboard')
    engine = engine_from_config(settings, 'sa.dashboard.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all()

    def generate_password():
        return base64.urlsafe_b64encode(os.urandom(30))

    with transaction.manager:
        session = DBSession()
        users = [
            add_user(session, u'admin@example.com', fullname='Administrator', password='admin@example.com'),
        ]

        role_admin = add_role(session, 'administrator')
        role_admin.users.append(users[0])

        add_role(session, 'external_developer')
        add_role(session, 'internal_developer')
        add_role(session, 'secretary')
        add_role(session, 'customer')
        add_role(session, 'project_manager')

        session.add(GlobalConfig(id=1))
