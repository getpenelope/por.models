import unittest
import transaction
from datetime import datetime
from pyramid import testing
from sqlalchemy.exc import IntegrityError
from por.models import DBSession, Base
from por.models.dashboard import Project, Application, CustomerRequest, Estimation 

def initTestingDB():
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

initTestingDB()

class DashboardSA_URITest(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        transaction.begin()

    def tearDown(self):
        Base.metadata.drop_all()
        Base.metadata.create_all()
        testing.tearDown()

    def test_sa_registration_validation(self):
        session = DBSession()
        application = Application(name=u'Trac')
        application.sa_uri = 'sqlite://'
        session.add(application)
        transaction.commit()


class DashboardModelsTest(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        transaction.begin()

    def tearDown(self):
        Base.metadata.drop_all()
        Base.metadata.create_all()
        testing.tearDown()

    def test_add_project(self):
        session = DBSession()
        project = Project(name=u'My first project')
        session.add(project)
        transaction.commit()
        self.assertEqual(session.query(Project).filter_by(name=u'My first project').first().name,'My first project')

    def test_project_creation_date(self):
        session = DBSession()
        project = Project(name=u'My first project A')
        session.add(project)
        transaction.commit()
        self.assertEqual(session.query(Project)\
                                .filter_by(name=u'My first project A')\
                                .first().creation_date.strftime('%Y%m%d'), datetime.now().strftime('%Y%m%d'))

    def test_add_duplicated_project(self):
        session = DBSession()
        project = Project(name=u'My project A')
        session.add(project)
        project = Project(name=u'My project A')
        session.add(project)
        self.assertRaises(IntegrityError, transaction.commit)
        session.rollback()

    def test_add_application_with_sa_to_project(self):
        session = DBSession()
        project = Project(name=u'My project 1')
        application = Application(name=u'Trac')
        project.add_application(application)
        session.add(project)
        transaction.commit()
        self.assertEqual(session.query(Project).filter_by(name=u'My project 1').first().applications[0].name, u'Trac')

    def test_application_position(self):
        session = DBSession()
        project1 = Project(id='sortedone')
        project2 = Project(id='sortedtwo')
        app1 = Application(name=u'First')
        app2 = Application(name=u'Second')
        app3 = Application(name=u'Third')
        app4 = Application(name=u'Fourth')
        app5 = Application(name=u'Fivth')
        project1.applications.append(app1)
        project1.applications.append(app2)
        project1.applications.append(app3)
        project2.applications.append(app4)
        project2.applications.append(app5)
        session.add(project1)
        session.add(project2)
        transaction.commit()
        self.assertEqual([a.position for a in session.query(Project).get('sortedone').applications], [0,1,2])
        self.assertEqual([a.position for a in session.query(Project).get('sortedtwo').applications], [0,1])
        project1 = session.query(Project).get('sortedone')
        app = project1.applications.pop(2)
        project1.applications.insert(0,app)
        transaction.commit()
        self.assertEqual([a.name for a in session.query(Project).get('sortedone').applications], [u'Third', u'First', u'Second'])

    def test_add_application_to_project(self):
        session = DBSession()
        project = Project(name=u'My project 2')
        application = Application(name=u'Trac', api_uri='http://simple.api.uri')
        project.add_application(application)
        session.add(project)
        transaction.commit()
        self.assertEqual(session.query(Project).filter_by(name=u'My project 2').first().applications[0].name, u'Trac')

    def test_add_duplicated_applications(self):
        project = Project(name=u'My project 3')
        application = Application(name=u'Trac')
        project.add_application(application)
        self.assertRaises(AttributeError, project.add_application,application)

    def test_add_primarykey_cr(self):
        session = DBSession()
        project1 = Project(name=u'My project 11')
        cr1 = CustomerRequest(name=u'My Customer reqeust 1')
        cr1.project = project1
        cr2 = CustomerRequest(name=u'My Customer reqeust 2')
        cr2.project = project1
        project2 = Project(name=u'My project 12')
        cr3 = CustomerRequest(name=u'My Customer reqeust 1')
        cr3.project = project2
        session.add(cr1)
        session.add(cr2)
        session.add(cr3)
        session.flush()
        self.assertTrue(cr1.id in ['my-project-11_2','my-project-11_1'])
        self.assertTrue(cr2.id in ['my-project-11_2','my-project-11_1'])
        self.assertEqual(cr3.id, 'my-project-12_1')

