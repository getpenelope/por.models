from por.models.dashboard import Project
from por.models import DBSession, Base
from datetime import datetime
import unittest
from pyramid import testing
import time
from sqlalchemy.exc import IntegrityError
import transaction


def initTestingDB():
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

initTestingDB()

class TPModelTest(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        transaction.begin()

    def tearDown(self):
        Base.metadata.drop_all()
        Base.metadata.create_all()
        testing.tearDown()

    def test_add_project(self):
        project_name = u'A project'
        session = DBSession()
        project = Project(name=project_name)
        session.add(project)
        transaction.commit()
        self.assertEqual(session.query(Project).filter_by(name=project_name).first().name, 'A project')

    def test_project_creation_date(self):
        project_name = u'B project'
        session = DBSession()
        project = Project(name=project_name)
        session.add(project)
        transaction.commit()
        self.assertEqual(session.query(Project).filter_by(name=project_name)\
                                               .first()\
                                               .creation_date.strftime('%Y%m%d'), datetime.now().strftime('%Y%m%d'))

    def test_project_modification_date(self):
        project_name = u'C project'
        session = DBSession()
        project = Project(name=project_name)
        session.add(project)
        transaction.commit()
        project = session.query(Project).filter_by(name=project_name).first()
        old_date = project.modification_date
        project.name = u'A modified project'
        time.sleep(0.1)
        transaction.commit()
        project = session.query(Project).filter_by(name=u'A modified project').first()
        new_date = project.modification_date
        self.assertNotEqual(old_date, new_date)

    def test_add_duplicated_project(self):
        session = DBSession()
        project = Project(name=u'My project A')
        session.add(project)
        transaction.commit()
        project = Project(name=u'My project A')
        session.add(project)
        self.assertRaises(IntegrityError, transaction.commit)
        session.rollback()

