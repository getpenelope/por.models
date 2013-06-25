import gspread
import getpass
import os
import sys
import transaction
import beaker

from sqlalchemy import engine_from_config
from pyramid.paster import setup_logging, bootstrap

from por.models.dbsession import DBSession
from por.models import Base
from por.models.dashboard import Contract, CustomerRequest
from por.models.tp import TimeEntry


beaker.cache.cache_regions.update(dict(calculate_matrix={'key_length':''}))


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)


def split_dict_equally(input_dict, chunks=10):
    "Splits dict by keys. Returns a list of dictionaries."
    # prep with empty dicts
    return_list = [dict() for idx in xrange(chunks)]
    idx = 0
    for k,v in input_dict.iteritems():
        return_list[idx][k] = v
        if idx < chunks-1:  # indexes start at 0
            idx += 1
        else:
            idx = 0
    return return_list


def update_time_entries():
    session = DBSession()

    tracs = {}
    time_entries = session.query(TimeEntry)
    for tp in time_entries:
        trac = list(tp.project.tracs)[0]
        tracs.setdefault(trac.trac_name, [])
        if not tp.ticket:
            print "TimeEntry %s has no ticket" % tp.id
            continue
        tracs[trac.trac_name].append((tp.id, tp.ticket))

    ticket_vs_crs = """SELECT value AS cr_id, '%(tp_id)s' AS tp_id FROM "trac_%(trac)s".ticket_custom WHERE name='customerrequest' AND ticket=%(ticket)s"""
    splitted_tracs = split_dict_equally(tracs)

    for split in splitted_tracs:
        queries = []
        for trac_id, opts in split.items():
            for opt in opts:
                queries.append(ticket_vs_crs % {'trac': trac_id,
                                                'tp_id': opt[0],
                                                'ticket': opt[1]})
        sql = '\nUNION '.join(queries)
        sql += ';'
        for trac in DBSession().execute(sql).fetchall():
            cr = session.query(CustomerRequest).get(trac.cr_id)
            if not cr:
                continue
            contract = cr.contract
            if not contract:
                continue
            tp = session.query(TimeEntry).get(trac.tp_id)
            if not tp:
                continue
            tp.contract_id = contract.id

def map_state(state):
    if state == 'A':
        return 'active'
    if state == 'B':
        return 'draft'
    if state == 'D':
        return 'done'
    return 'draft'


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)
    env = bootstrap('%s#dashboard'% config_uri)
    settings = env.get('registry').settings
    engine = engine_from_config(settings, 'sa.dashboard.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    google_user = raw_input('Google Spreadsheet User: ')
    google_password = getpass.getpass("Google Spreadsheet Password: ")
    spreadsheet_key = raw_input('Google Spreadsheet ID: ')

    gc = gspread.login(google_user, google_password)
    sht = gc.open_by_key(spreadsheet_key)
    worksheet = sht.get_worksheet(0)
    crs = worksheet.get_all_records()

    contracts = {}
    for row in crs:
        if not row['titolocommessa']:
            continue
        contracts.setdefault(row['titolocommessa'], {'crs':[]})
        contracts[row['titolocommessa']]['nrcontratto'] = row['nrcontratto']
        contracts[row['titolocommessa']]['gg'] = row['gg'] or 0
        contracts[row['titolocommessa']]['amount'] = row['amount'] or 0
        contracts[row['titolocommessa']]['crs'].append(row['cr_id'])
        contracts[row['titolocommessa']]['stato'] = map_state(row['stato'])

    # now we have a structure:
    # contracts['Contract name'] = {'crs': ['customer_request_id_1',
    #                                       'customer_request_id_2'],
    #                               'gg': '12'}

    with transaction.manager:
        session = DBSession()
        for contract_name, opts in contracts.items():
            crs = [session.query(CustomerRequest).get(a) for a in opts['crs']]

            #contract = session.query(Contract).filter_by(name=contract_name).first()
            contract = crs[0].contract
            if not contract:
                contract = Contract(name=contract_name)
            contract.days = opts['gg']
            contract.ammount = opts['amount']
            contract.contract_number = opts['nrcontratto']
            contract.workflow_state = opts['stato']
            for cr in crs:
                if not cr:
                    continue
                cr.contract = contract
                contract.project_id = cr.project_id

        update_time_entries()
