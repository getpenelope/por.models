# -*- coding: utf-8 -*-

import xmlrpclib

from copy import deepcopy
from zope.interface import implements
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Interval
from sqlalchemy import Unicode
from sqlalchemy import String
from sqlalchemy import event
from sqlalchemy.orm import relationship, backref

from por.models.dublincore import dublincore_insert, dublincore_update, DublinCore
from por.models import Base, DBSession, CustomerRequest
from por.models import workflow, classproperty
from por.models.tickets import ticket_store
from por.models.interfaces import ITimeEntry, IProjectRelated
from por.dashboard.security.acl import CRUD_ACL


class TimeEntryException(Exception):
    """Something wrong happened trying to add a time entry to a project"""

SECS_IN_HR = 60.0*60.0
WORK_HOURS_IN_DAY = 8.0


def timedelta_as_work_days(td):
    return (td.days*24.0 + td.seconds/SECS_IN_HR) / WORK_HOURS_IN_DAY


def timedelta_as_human_str(td, seconds=False):
    """
    Formats a timedelta for human consumption. Also used by some reports.
    """
    if td is None:
        return ''
    hh, rem = divmod(td.days*24.0*SECS_IN_HR + td.seconds, SECS_IN_HR)
    mm, ss = divmod(rem, 60)
    if seconds or ss:
        return '%d:%02d:%02d' % (hh, mm, ss)
    else:
        return '%d:%02d' % (hh, mm)


class TimeEntry(DublinCore, workflow.Workflow, Base):
    implements(ITimeEntry, IProjectRelated)
    __tablename__ = 'time_entries'

    id = Column(Integer, primary_key=True)
    start = Column(DateTime)
    end = Column(DateTime)
    date = Column(Date, index=True)
    hours = Column(Interval)
    description = Column(Unicode)
    location = Column(Unicode, nullable=False, default=u'RedTurtle')
    ticket = Column(Integer, index=True)
    tickettype = Column(String(25))
    invoice_number = Column(String(10))

    contract_id = Column(String, ForeignKey('contracts.id'), index=True, nullable=True)
    contract = relationship('Contract', uselist=False, backref=backref('time_entries', order_by=id))

    project_id = Column(String, ForeignKey('projects.id'), index=True, nullable=False)
    project = relationship('Project', uselist=False, backref=backref('time_entries', order_by=id))

    @classproperty
    def __acl__(cls):
        acl = deepcopy(CRUD_ACL)
        #add
        acl.allow('role:local_developer', 'new')
        acl.allow('role:local_project_manager', 'new')
        acl.allow('role:external_developer', 'new')
        acl.allow('role:internal_developer', 'new')
        acl.allow('role:secretary', 'new')
        acl.allow('role:project_manager', 'new')
        #view
        acl.allow('role:owner', 'view')
        acl.allow('role:project_manager', 'view')
        acl.allow('role:internal_developer', 'view')
        #edit
        acl.allow('role:project_manager', 'edit')
        acl.allow('role:secretary', 'manage')
        #delete
        isnew = bool(cls.workflow_state == u'new')
        if isnew: #only in new state
            acl.allow('role:owner', 'edit')
            acl.allow('role:owner', 'delete')
        acl.allow('role:project_manager', 'delete')
        #workflow
        acl.allow('role:secretary', 'workflow')
        acl.allow('role:project_manager', 'workflow')
        #listing
        acl.allow('role:project_manager', 'listing')
        return acl

    def __init__(self, *args, **kwargs):
        super(TimeEntry, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.__unicode__().encode('utf8')

    def __unicode__(self):
        return self.plaintext_description

    @property
    def plaintext_description(self):
        return self.description or ''

    @property
    def hours_str(self):
        return timedelta_as_human_str(self.hours)

    @property
    def hours_as_work_days(self):
        return timedelta_as_work_days(self.hours)

    def get_ticket(self, request=None):
        request = request or getattr(self, 'request', None)
        return ticket_store.get_ticket(request, self.project_id, self.ticket)

    def get_ticket_summary(self, request=None):
        ticket = self.get_ticket(request)
        if ticket:
            return ticket[3]['summary']


def new_te_created(mapper, connection, target):
    try:
        trac_ticket = target.get_ticket()
    except xmlrpclib.Error:
        pass
    else:
        if trac_ticket:
            target.tickettype = trac_ticket[3]['type']
            contract_id = DBSession().query(CustomerRequest)\
                                     .get(trac_ticket[3]['customerrequest'])\
                                     .contract_id
            target.contract_id = contract_id


event.listen(TimeEntry, "before_insert", new_te_created)
event.listen(TimeEntry, "before_insert", dublincore_insert)
event.listen(TimeEntry, "before_update", dublincore_update)
