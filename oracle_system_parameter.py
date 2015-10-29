#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: oracle_system_parameter
short_description: Manage Oracle system parameters
description:
- Modify Oracle system parameters
options:
  name:
    description: Parameter name
    required: true
  value:
    description: Parameter value
    required: true
  scope:
    description:
    default: both
    choices: ["both", "memory", "spfile"]
  state:
    description: Parameter state
    required: False
    default: present
    choices: ["present", "absent"]
  oracle_host:
    description: Hostname or IP address of Oracle DB
    required: False
    default: 127.0.0.1
  oracle_port:
    description: Listener Port
    required: False
    default: 1521
  oracle_user:
    description: Account to connect as
    required: False
    default: SYSTEM
  oracle_pass:
    description: Password to be used to authenticate
    required: False
    default: manager
  oracle_service:
    description: Service name to connect to
    required: False
    default: ORCL
notes:
- Requires cx_Oracle
#version_added: "2.0"
author: "Thomas Krahn (@nosmoht)"
'''

try:
    import cx_Oracle
except ImportError:
    oracleclient_found = False
else:
    oracleclient_found = True


def createConnection(username, userpass, host, port, service):
    return cx_Oracle.connect('{username}/{userpass}@{host}:{port}/{service}'.format(username=username, userpass=userpass, host=host, port=port, service=service))


def executeSQL(sql):
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except cx_Oracle.DatabaseError as e:
        module.fail_json(msg='{sql}: {err}'.format(sql=sql, err=e))
    cur.close()


def getSystemParameter(name):
    data = None
    cur = conn.cursor()
    try:
        cur.prepare('select sp.name, sp.value, sp.display_value from v$system_parameter sp where sp.name = :name')
        cur.execute(None, dict(name=name))
        row = cur.fetchone()
        if row:
            data = dict(name=row[0],value=row[1],display_value=row[2])
        cur.close()
        return data
    except cx_Oracle.DatabaseError as e:
        module.fail_json(msg='Error: {err}'.format(err=str(e)))


def getAlterSystemSQL(name, value, scope, reset=False):
    if reset:
        sql = "ALTER SYSTEM RESET '{name}' SCOPE={scope}".format(name=name,scope=scope)
    else:
        sql = "ALTER SYSTEM SET {name}='{value}' SCOPE={scope}".format(name=name,value=value,scope=scope)
    return sql


def ensure():
    changed = False

    name = module.params['name'].lower()
    value = module.params['value']
    scope = module.params['scope']
    state = module.params['state']

    data = getSystemParameter(name)
    sql = None
    if data:
        if state == 'absent' and data.get('value') != '':
            sql = getAlterSystemSQL(name=name, scope=scope,reset=True)
        if value not in [data.get('value'),data.get('display_value')]:
            sql = getAlterSystemSQL(name=name,value=value,scope=scope,reset=False)
        if sql:
            executeSQL(sql)
            changed = True
            data=getSystemParameter(name=name)
    return changed, data


def main():
    global module
    global conn

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            value=dict(type='str', required=False),
            scope=dict(type='str', default='both', choices=["both", "memory", "spfile"]),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            oracle_host=dict(type='str', default='127.0.0.1'),
            oracle_port=dict(type='str', default='1521'),
            oracle_user=dict(type='str', default='SYSTEM'),
            oracle_pass=dict(type='str', default='manager'),
            oracle_service=dict(type='str', default='ORCL'),
        ),
    )

    if not oracleclient_found:
        module.fail_json(
            msg='cx_Oracle not found. Needs to be installed. See http://cx-oracle.sourceforge.net/')

    oracle_host = module.params['oracle_host']
    oracle_port = module.params['oracle_port']
    oracle_user = module.params['oracle_user']
    oracle_pass = module.params['oracle_pass']
    oracle_service = module.params['oracle_service']

    try:
        conn = createConnection(username=oracle_user, userpass=oracle_pass,
                                host=oracle_host, port=oracle_port, service=oracle_service)
    except cx_Oracle.DatabaseError as e:
        module.fail_json(msg=str(e))

    changed, system_parameter = ensure()
    module.exit_json(changed=changed, system_parameter=system_parameter)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()