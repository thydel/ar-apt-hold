#!/usr/bin/python

DOCUMENTATION = '''
#include documentation.yml
'''

EXAMPLES = '''
#include examples.yml
'''

def main():
    
    argument_spec = dict(
        hold = dict(required=False, choices=BOOLEANS, type='bool', default=True),
        search = dict(required=False, type='list', default=[]),
        notfoundok = dict(required=False, choices=BOOLEANS, type='bool', default=False),
        )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    changed = False
    info = {}
    ansible_facts = { 'apt_hold': info }

    def getargs(arg):
        info[arg] = globals()[arg] = module.params.get(arg)
        
    # all(map(getargs, argument_spec.keys()))
    for arg in argument_spec.keys():
        getargs(arg)

    if (len(search) == 1 and search[0] == ''):
        del search[0]

    cmd_apt                 = ["/usr/bin/env", "aptitude"]
    cmd_search = cmd_apt    + ["--disable-columns", "-F", "%p", "search"]

    cmd_held   = cmd_search + ["~ahold"]
    cmd_find   = cmd_search + search

    cmd_hold   = cmd_apt    + ["hold"]
    cmd_unhold = cmd_apt    + ["unhold"]

    # get the list of held packages

    rc, out, err = module.run_command(cmd_held, check_rc=False)
    # jessie aptitude 0.6.11 search return 0 for no result search
    # stretch aptitude 0.8.7 search return 1 for no result search
    if (rc == -1):
        msg = "aptitude return -1"
        module.fail_json(cmd=clean_args, rc=rc, stdout=stdout, stderr=stderr, msg=msg)
    held = out.split()
    info['held'] = held

    # find a list of packages

    found = []
    if search:
        rc, out, err = module.run_command(cmd_find, check_rc=True)
        found = out.split()
        info['found'] = found

    # if no hold arg return facts
    
    if hold is None or (not found and notfoundok):
        module.exit_json(changed=changed, ansible_facts=ansible_facts)

    # either hold or unhold found packages

    if not found:
        module.fail_json(msg="Can't hold or unhold an empty packages list")
        
    if hold:
        cmd = cmd_hold
        diff = sorted(list(set(found).difference(held)))
    else:
        cmd = cmd_unhold
        diff = sorted(list(set(found).intersection(held)))

    if diff:
        changed = True
        info['diff'] = diff
        if module.check_mode:
            module.exit_json(changed=changed, ansible_facts=ansible_facts)
        rc, out, err = module.run_command(cmd + diff, check_rc=True)

    module.exit_json(changed=changed, ansible_facts=ansible_facts)

from ansible.module_utils.basic import *

main()
