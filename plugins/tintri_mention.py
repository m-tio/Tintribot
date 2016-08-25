# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Masayuki Ito.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import re
import tintri_operation_v1 as tintri_op
import tintri_1_1 as tintri
from slackbot.bot import respond_to
from slackbot.bot import listen_to

@respond_to(u'^ *help', re.IGNORECASE)
def show_help(message):
    helpmsg = (u'\n'
               'Usage:\n'
               '@botname:tintri [TintriHostName] show... Show {appliance_info, dashboard, alert, vmlist, help} status.\n'
               '@botname:tintri [TintriHostName] {command} help... Show {command} help.\n'
               '\n'
               )
    message.reply(helpmsg)

# Change following line.
# plugins/tintri_operation_v1.py
#@respond_to(u'{vmstores['VMStore-Name']}.* (.*)', re.IGNORECASE)
#@respond_to(u'tintri.* (.*)', re.IGNORECASE)
@respond_to(u'tintri (.*)', re.IGNORECASE) #fix 20160819 "u'tintri.*" to "u'tintri"
def tintri_command(message, *args):
    msg = message.body['text'].split()
    if len(msg) > 3 and re.compile('show', re.IGNORECASE).search(msg[2]):
        info = get_info(msg)
        message.reply(info)
    else:
        show_help(message)

def get_info(args):
    # Get Login info
    vmstore = tintri_op.get_VMStore_info(args[1])
    helpmsg = '\n' + (u'Usage:\n'
                     '@botname:tintri [TintriHostName] show appliance_info... Show appliance infomation.\n'
                     '@botname:tintri [TintriHostName] show dashboard... Show dashboard.\n'
                     '@botname:tintri [TintriHostName] show alert... Show alerts and notices.\n'
                     '@botname:tintri [TintriHostName] show vmlist... Show vm list in VMStore.\n'
                     '@botname:tintri [TintriHostName] show vmlist search [VMName(Regular expression)]... Show vm list of [VMName] in VMStore.\n'
                     '\n'
                     '@botname:tintri [TintriHostName] {command} help... Show {command} help.\n')

    m = re.compile('help|appliance_info|dashboard|alert|vmlist', re.I).search(args[3])

    com = None
    if m:
        com = m.group().lower()
    else:
        return helpmsg

    if len(args) <= 3 or com == 'help':
        return helpmsg

    elif len(args) > 3:
        # Connect to VMStore
        session_id = tintri_op.tintri_login(vmstore[1], vmstore[2], vmstore[3])
    table = None

    if com == 'appliance_info':
            # Get json info
            json_info = tintri_op.get_json_info(vmstore[1])
            # Get appliance info
            appliance_info = tintri_op.get_appliance_info(vmstore[1], session_id)
            # Create appliance info table
            table = tintri_op.create_appliance_info_table(json_info, appliance_info)

    elif com == 'dashboard':
            # Get dashboard info
            dashboard_info = tintri_op.get_dashboard_info(vmstore[1], session_id)
            # Create dashboard info table
            table = tintri_op.create_dashboard_info_table(dashboard_info)

    elif com == 'alert':
        # get alerts and notices
            alerts_notices = tintri_op.get_alerts_notices(vmstore[1], session_id)
            # create alerts and notices table
            table = tintri_op.create_alerts_notices_table(alerts_notices)

    elif com == 'vmlist':
        # Get dashboard info
        vms = tintri_op.get_vms(vmstore[1], session_id)
        # Create dashboard info table
        if len(args) == 6 and re.compile('search', re.IGNORECASE).search(args[4]):
            table = tintri_op.create_vmstats_table(vms, args[5])
        else:
            table = tintri_op.create_vmstats_table(vms)

        # Logout
        tintri_op.tintri_logout(vmstore[1], session_id)

    if table:
        ret = '\n```' + str(table) + '```'
        print 'ret: ', ret
        return ret
    else:
        return helpmsg
