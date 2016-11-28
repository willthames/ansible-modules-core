#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: rds_facts
version_added: "2.3"
short_description: obtain facts about one or more RDS instances
description:
  - obtain facts about one or more RDS instances
options:
  instance_name:
    description:
      - one or more comma separated names of RDS instances
    required: false
requirements:
    - "python >= 2.6"
    - "boto3"
author:
    - "Bruce Pennypacker (@bpennypacker)"
    - "Will Thames (@willthames)"
extends_documentation_fragment:
    - aws
    - ec2
'''

# FIXME: the command stuff needs a 'state' like alias to make things consistent -- MPD

EXAMPLES = '''
# Get facts about an instance
- rds_facts:
    instance_name: new-database
  register: new_database_facts
'''


try:
    import boto3.rds
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class RDSConnection:
    def __init__(self, module, region, **aws_connect_params):
        try:
            self.connection  = connect_to_aws(boto.rds, region, **aws_connect_params)
        except boto.exception.BotoServerError as e:
             module.fail_json(msg=e.error_message)

    def get_db_instance(self, instancename):
        try:
            return RDSDBInstance(self.connection.get_all_dbinstances(instancename)[0])
        except boto.exception.BotoServerError as e:
            return None

    def get_db_snapshot(self, snapshotid):
        try:
            return RDSSnapshot(self.connection.get_all_dbsnapshots(snapshot_id=snapshotid)[0])
        except boto.exception.BotoServerError as e:
            return None


def facts_db_instance_or_snapshot(module, conn):
    instance_name = module.params.get('instance_name')
    snapshot = module.params.get('snapshot')

    if instance_name and snapshot:
        module.fail_json(msg="rds_facts must be called with either instance_name or snapshot, not both")
    if instance_name:
        resource = get_db_instance(instance_name)
        if not resource:
            module.fail_json(msg="DB instance %s does not exist" % instance_name)
    if snapshot:
        resource = get_db_snapshot(snapshot)
        if not resource:
            module.fail_json(msg="DB snapshot %s does not exist" % snapshot)

    module.exit_json(changed=False, instance=resource.get_data())


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            instance_name = dict(required=False),
            snapshot = dict(required=False),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg="Region not specified. Unable to determine region from configuration.")

    # connect to the rds endpoint
    conn = connect_to_aws(boto3.rds, region, **aws_connect_params)

    facts_db_instance_or_snapshot(module, conn)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
