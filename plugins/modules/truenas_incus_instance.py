#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chad Pritchett
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# Manage Incus instances on TrueNAS SCALE 25.04+

DOCUMENTATION = r'''
---
module: truenas_incus_instance

short_description: Manage Incus instances on TrueNAS SCALE 25.04+

version_added: "1.0.0"

description:
    - Manage Incus LXC containers and VMs on TrueNAS SCALE 25.04 (Fangtooth) or later
    - Uses the TrueNAS API /virt/instance endpoints
    - This module should be contributed to github.com/cpritchett/ansible-truenas

options:
    name:
        description:
            - Name of the Incus instance
        required: true
        type: str
    state:
        description:
            - Desired state of the instance
        choices: ['present', 'absent', 'started', 'stopped', 'restarted']
        default: present
        type: str
    type:
        description:
            - Type of instance to create
        choices: ['CONTAINER', 'VM']
        default: CONTAINER
        type: str
    source:
        description:
            - Source for the instance
        type: dict
        suboptions:
            type:
                description: Source type
                choices: ['IMAGE', 'MIGRATION', 'COPY', 'NONE']
                default: IMAGE
                type: str
            alias:
                description: Image alias (e.g., debian/12, ubuntu/22.04)
                type: str
            server:
                description: Image server URL
                default: https://images.linuxcontainers.org
                type: str
    config:
        description:
            - Instance configuration options
        type: dict
    devices:
        description:
            - Instance devices (disks, nics, proxies, etc.)
        type: dict
    wait_for_ipv4:
        description:
            - Wait for instance to get IPv4 address
        default: false
        type: bool
    timeout:
        description:
            - Timeout for operations in seconds
        default: 60
        type: int

extends_documentation_fragment:
    - arensb.truenas.truenas

author:
    - Chad Pritchett (@cpritchett)
'''

EXAMPLES = r'''
# Create a Debian 12 container
- name: Create Matchbox container
  truenas_incus_instance:
    name: matchbox
    type: CONTAINER
    source:
      type: IMAGE
      alias: debian/12
    config:
      limits.cpu: "2"
      limits.memory: "2GB"
      boot.autostart: "true"
    devices:
      root:
        type: disk
        path: /
        pool: default
        size: 20GB
      eth0:
        type: nic
        network: incusbr0

# Start an instance
- name: Start container
  truenas_incus_instance:
    name: matchbox
    state: started

# Delete an instance
- name: Remove container
  truenas_incus_instance:
    name: matchbox
    state: absent
'''

RETURN = r'''
instance:
    description: The instance information
    type: dict
    returned: always
    sample: {
        "id": "123",
        "name": "matchbox",
        "status": "Running",
        "type": "CONTAINER"
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.arensb.truenas.plugins.module_utils.rest_api import RestApiClient
import time


def get_instance(api_client, name):
    """Get instance by name"""
    response = api_client.call('/virt/instance', method='GET')

    if response.status_code == 200:
        instances = response.json()
        for instance in instances:
            if instance.get('name') == name:
                return instance
    return None


def create_instance(module, api_client):
    """Create a new Incus instance"""
    payload = {
        'name': module.params['name'],
        'type': module.params['type']
    }

    if module.params['source']:
        payload['source'] = module.params['source']

    if module.params['config']:
        payload['config'] = module.params['config']

    if module.params['devices']:
        payload['devices'] = module.params['devices']

    response = api_client.call('/virt/instance', method='POST', data=payload)

    if response.status_code in [200, 201]:
        return True, response.json()
    else:
        module.fail_json(msg=f"Failed to create instance: {response.text}")


def delete_instance(module, api_client, instance_id):
    """Delete an instance"""
    # Stop instance first if running
    stop_instance(module, api_client, instance_id)

    response = api_client.call(f'/virt/instance/{instance_id}', method='DELETE')

    if response.status_code in [200, 204]:
        return True
    else:
        module.fail_json(msg=f"Failed to delete instance: {response.text}")


def start_instance(module, api_client, instance_id):
    """Start an instance"""
    response = api_client.call(f'/virt/instance/{instance_id}/start', method='POST')

    if response.status_code in [200, 202, 409]:  # 409 if already running
        return True
    else:
        module.fail_json(msg=f"Failed to start instance: {response.text}")


def stop_instance(module, api_client, instance_id):
    """Stop an instance"""
    response = api_client.call(f'/virt/instance/{instance_id}/stop', method='POST')

    if response.status_code in [200, 202, 409]:  # 409 if already stopped
        return True
    else:
        module.fail_json(msg=f"Failed to stop instance: {response.text}")


def restart_instance(module, api_client, instance_id):
    """Restart an instance"""
    response = api_client.call(f'/virt/instance/{instance_id}/restart', method='POST')

    if response.status_code in [200, 202]:
        return True
    else:
        module.fail_json(msg=f"Failed to restart instance: {response.text}")


def wait_for_state(api_client, name, desired_state, timeout):
    """Wait for instance to reach desired state"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        instance = get_instance(api_client, name)
        if instance and instance.get('status') == desired_state:
            return True
        time.sleep(2)

    return False


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(
            type='str',
            choices=['present', 'absent', 'started', 'stopped', 'restarted'],
            default='present'
        ),
        type=dict(
            type='str',
            choices=['CONTAINER', 'VM'],
            default='CONTAINER'
        ),
        source=dict(type='dict', required=False),
        config=dict(type='dict', required=False),
        devices=dict(type='dict', required=False),
        wait_for_ipv4=dict(type='bool', default=False),
        timeout=dict(type='int', default=60),
        api_url=dict(type='str', required=False, default='https://localhost/api/v2.0'),
        api_key=dict(type='str', required=False, no_log=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Initialize REST API client
    api_client = RestApiClient(
        module,
        api_url=module.params.get('api_url'),
        api_key=module.params.get('api_key')
    )

    name = module.params['name']
    state = module.params['state']

    # Get current instance state
    instance = get_instance(api_client, name)

    changed = False
    result = {'changed': False, 'instance': {}}

    if state == 'present':
        if not instance:
            if not module.check_mode:
                changed, instance = create_instance(module, api_client)
                # Auto-start if boot.autostart is true
                if instance and module.params.get('config', {}).get('boot.autostart') == 'true':
                    start_instance(module, api_client, instance['id'])
            else:
                changed = True
        result['instance'] = instance or {}

    elif state == 'absent':
        if instance:
            if not module.check_mode:
                changed = delete_instance(module, api_client, instance['id'])
            else:
                changed = True

    elif state == 'started':
        if instance:
            if instance.get('status') != 'Running':
                if not module.check_mode:
                    changed = start_instance(module, api_client, instance['id'])
                    wait_for_state(api_client, name, 'Running', module.params['timeout'])
                else:
                    changed = True
            result['instance'] = instance
        else:
            module.fail_json(msg=f"Instance {name} does not exist")

    elif state == 'stopped':
        if instance:
            if instance.get('status') != 'Stopped':
                if not module.check_mode:
                    changed = stop_instance(module, api_client, instance['id'])
                    wait_for_state(api_client, name, 'Stopped', module.params['timeout'])
                else:
                    changed = True
            result['instance'] = instance
        else:
            module.fail_json(msg=f"Instance {name} does not exist")

    elif state == 'restarted':
        if instance:
            if not module.check_mode:
                changed = restart_instance(module, api_client, instance['id'])
                wait_for_state(api_client, name, 'Running', module.params['timeout'])
            else:
                changed = True
            result['instance'] = instance
        else:
            module.fail_json(msg=f"Instance {name} does not exist")

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
