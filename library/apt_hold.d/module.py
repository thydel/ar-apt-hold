#!/usr/bin/python

DOCUMENTATION = '''
#include documentation.yml
'''

EXAMPLES = '''
#include examples.yml
'''

def main():
    
    argument_spec = dict(
        hold = dict(required=False, choices=BOOLEANS, type='bool'),
        search = dict(required=False),
        notfoundok = dict(required=False, default='no', choices=BOOLEANS, type='bool'),
        )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    changed = False
    info = {}
    ansible_facts = { 'apt_hold': info }

    def getargs(arg):
        info[arg] = globals()[arg] = module.params.get(arg)
        
    map(getargs, argument_spec.keys())

    search_list = []
    if search:
        if type(search) is str:
            info['search'] = search_list = [search]
        else:
            search_list = search

    cmd_apt                 = ["/usr/bin/env", "aptitude"]
    cmd_search = cmd_apt    + ["--disable-columns", "-F", "%p", "search"]

    cmd_held   = cmd_search + ["~ahold"]
    cmd_find   = cmd_search + search_list

    cmd_hold   = cmd_apt    + ["hold"]
    cmd_unhold = cmd_apt    + ["unhold"]

    # get the list of held packages

    rc, out, err = module.run_command(cmd_held, check_rc=True)
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

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
