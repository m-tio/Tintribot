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
import tintri_1_1 as tintri
import requests
import json
import sys
import time
from datetime import date, datetime
from prettytable import PrettyTable

#disable security warnings
requests.packages.urllib3.disable_warnings()

# For exhaustive messages on console, make it to True; otherwise keep it False
debug_mode = False


def get_VMStore_info(vmstorename):
    vmstores = {}
    # VMStore list
    # vmstores['VMStore-Name'] = ('VMStore-IP/Name', 'VMStoreUser', 'VMStorePass')
    vmstores['tintri-001'] = ('192.168.1.x', 'admin', 'tintri')
    vmstores['tintri-002'] = ('192.168.2.x', 'admin', 'tintri')

    for vmstore in vmstores:
        if re.compile(vmstore, re.IGNORECASE).search(vmstorename):
            VMStoreNAME = vmstore
            VMStoreIP   = vmstores[vmstore][0]
            VMStoreUSER = vmstores[vmstore][1]
            VMStorePASS = vmstores[vmstore][2]
            break

    if VMStoreNAME and VMStoreIP and VMStoreUSER and VMStorePASS:
        vmstoreinfo = (VMStoreNAME, VMStoreIP, VMStoreUSER, VMStorePASS)
    else:
        vmstoreinfo = ()

    return vmstoreinfo

def tintri_login(vmstore, user, password):
    # Login and get session_id
    try:
        ret = tintri.api_version(vmstore)
        json_info = ret.json()
        print_info("API Version: " + json_info['preferredVersion'])

        # Login to VMstore
        session_id = tintri.api_login(vmstore, user, password)

        return session_id

    except tintri.TintriRequestsException as tre:
        print_error(tre.__str__())
        exit(-1)
    except tintri.TintriApiException as tae:
        print_error(tae.__str__())
        exit(-2)


def tintri_logout(vmstore, session_id):
    # Logout
    tintri.api_logout(vmstore, session_id)


def get_info(vmstore, session_id, url):
    try:
        # Get infomation from api
        ret = tintri.api_get(vmstore, url, session_id)
        print_debug("The JSON response of the get invoke to the server " +
                    vmstore + " is: " + ret.text)
        return ret.json()

    except tintri.TintriRequestsException as tre:
        print_error(tre.__str__())
        tintri.api_logout(vmstore, session_id)
        exit(-10)
    except tintri.TintriApiException as tae:
        print_error(tae.__str__())
        tintri.api_logout(vmstore, session_id)
        exit(-11)


# Holds VM name, UUID, and statistics.
class VmStat:
    def __init__(self, name, uuid, stats):
        self.name = name
        self.uuid = uuid
        self.stats = stats


    def get_stat(self, stat):
        if stat in self.stats:
            return self.stats[stat]
        return None

# Print functions
def print_with_prefix(prefix, out):
    print(prefix + out)
    return


def print_debug(out):
    if debug_mode:
        print_with_prefix("[DEBUG] : ", out)
    return


def print_info(out):
    print_with_prefix("[INFO] : ", out)
    return


def print_error(out):
    print_with_prefix("[ERROR] : ", out)
    return


# Returns a dictionary of live VM objects with statistics with
# the VM name as the key.
def get_vms(vmstore, session_id):

    page_size = 25  # default

    # dictionary of VM objects
    vms = {}

    # Get a list of VMs a page size at a time
    get_vm_url = "/v310/vm"
    count = 1
    vm_paginated_result = {'live' : "TRUE",
                           'next' : "offset=0&limit=" + str(page_size)}

    # While there are more VMs, go get them
    while 'next' in vm_paginated_result:
        url = get_vm_url + "?" + vm_paginated_result['next']

        # This is a work-around for a TGC bug.
        chop_i = url.find("&replicationHasIssue")
        if chop_i != -1:
            url = url[:chop_i]
            print_debug("Fixing URL")

        print_debug("Next GET VM URL: " + str(count) + ": " + url)

        # Invoke the API
        ret = tintri.api_get(vmstore, url, session_id)
        print_debug("The JSON response of the get invoke to the server " +
                    vmstore + " is: " + ret.text)

        # if HTTP Response is not 200 then raise an error
        if ret.status_code != 200:
            print_error("The HTTP response for the get invoke to the server " +
                  vmstore + " is not 200, but is: " + str(ret.status_code))
            print_error("url = " + url)
            print_error("response: " + ret.text)
            tintri.api_logout(vmstore, session_id)
            sys.exit(-10)

        # For each VM in the page, print the VM name and UUID.
        vm_paginated_result = ret.json()

        # Check for the first time through the loop and
        # print the total number of VMs.
        if count == 1:
            num_filtered_vms = vm_paginated_result["filteredTotal"]
            if num_filtered_vms == 0:
                print_error("No VMs present")
                tintri.api_logout(vmstore, session_id)
                sys_exit(-99)

        # Get and store the VM items and save in a VM object.
        items = vm_paginated_result["items"]
        for vm in items:
            vm_name = vm["vmware"]["name"]
            vm_uuid = vm["uuid"]["uuid"]
            vm_stats = VmStat(vm_name, vm_uuid, vm["stat"]["sortedStats"][0])
            print_debug(str(count) + ": " + vm_name + ", " + vm_uuid)
            count += 1
            # Store the VM stats object keyed by VM name.
            vms[vm_name] = vm_stats

    return vms


def create_vmstats_table(vms, vmname=None):

    if vmname is None or re.compile(vmname, re.IGNORECASE) == 'all':
        vmname = '.'

    # Define the statistic fields to display.  The fields can be changed
    # without modifying the print code below.  See the API documentation
    # for more statistic fields.
    #stat_fields = ['spaceUsedGiB', 'operationsTotalIops', 'latencyTotalMs']
    stat_fields = ['flashHitPercent', 'operationsTotalIops', 'throughputTotalMBps', 'latencyTotalMs', 'spaceUsedGiB']

    # Create the table header with the fields
    table_header = ["VM name"]
    for field in stat_fields:
        table_header.append(field)

    table = PrettyTable(table_header)
    table.align["VM name"] = "l"

    # Build the table rows based on the statistic fields
    for key, value in sorted(vms.items()):
        print_debug(key + " " + value.uuid)
        vm = value.name
        # Filtering VMName
        if re.search('.*' + str(vmname) + '.*', str(vm), re.IGNORECASE):
            row = [vm]
            for field in stat_fields:
                stat = value.get_stat(field)
                if stat is None:
                    row.append("---")
                else:
                    row.append(stat)
            table.add_row(row)

    # Return the table
    return table


def get_appliance_info(vmstore, session_id):
    # Get appliance info
    url = "/v310/appliance/default/info"
    ret = get_info(vmstore, session_id, url)

    return ret


def get_json_info(vmstore):
    try:
        # Get json info
        ret = tintri.api_version(vmstore)
        return ret.json()

    except tintri.TintriRequestsException as tre:
        print_error(tre.__str__())
        tintri.api_logout(vmstore, session_id)
        exit(-10)
    except tintri.TintriApiException as tae:
        print_error(tae.__str__())
        tintri.api_logout(vmstore, session_id)
        exit(-11)


def create_appliance_info_table(json_info, appliance_info):
    # Some OS versions do not return all flash.
    all_flash = False
    show_all_flash = False

    if 'isAllFlash' in appliance_info:
        all_flash = appliance_info['isAllFlash']
        show_all_flash = True

    table_header = ('Info', 'Value')
    table = PrettyTable(table_header)
    table.align['Info'] = "l"
    table.align['Value'] = "l"

    product_name = json_info['productName']
    row = ('Product', product_name)
    table.add_row(row)

    row = ('Model', appliance_info['modelName'])
    table.add_row(row)

    if show_all_flash:
        row = ('All Flash', all_flash)
        table.add_row(row)

    row = ('OS version', appliance_info['osVersion'])
    table.add_row(row)

    row = ('API version', json_info['preferredVersion'])
    table.add_row(row)

    return table


def get_dashboard_info(vmstore,session_id):
    # Get dashboard info
    url = "/v310/datastore/default/statsRealtime"
    ret = get_info(vmstore, session_id, url)

    return ret


def create_dashboard_info_table(dashboard_info):
    # get the filteredtotal number of datastore stats
    number_of_dsStats=int(dashboard_info['filteredTotal'])

    #Printing datastore stat in tabular format
    if number_of_dsStats > 0:
        header = ['Flash hit Ratio (%)', 'Network latency (ms)', 'Storage latency (ms)',
                  'Disk latency (ms)', 'Host latency (ms)', 'Total latency (ms)',
                  'Perf. Reserves allocated', 'Space used live Physical (GiB)', 'Space used other (GiB)',
                  'Read IOPS', 'Write IOPS', 'Throughput Read (MBps)', 'Throughput Write (MBps)']
        stats = dashboard_info["items"][0]["sortedStats"]

        table = PrettyTable()
        table.add_column("Attributes", header)
        table.add_column("Values", [stats[0]["flashHitPercent"], stats[0]["latencyNetworkMs"],
                                    stats[0]["latencyStorageMs"], stats[0]["latencyDiskMs"],
                                    stats[0]["latencyHostMs"], stats[0]["latencyTotalMs"],
                                    stats[0]["performanceReserveAutoAllocated"],
                                    stats[0]["spaceUsedLivePhysicalGiB"],
                                    stats[0]["spaceUsedOtherGiB"],
                                    stats[0]["operationsReadIops"], stats[0]["operationsWriteIops"],
                                    stats[0]["throughputReadMBps"], stats[0]["throughputWriteMBps"]
                                    ]
        )
    return table


def get_alerts_notices(vmstore,session_id):
    # Get inbox alert info
    url = "/v310/alert"
    ret = get_info(vmstore, session_id, url)

    return ret


def create_alerts_notices_table(alerts_notices):

    # Number of items to display on bot
    number_of_items_to_display_on_bot = 20

    # get the filteredtotal number of inbox-ed alert
    number_of_alerts_notices = int(alerts_notices["filteredTotal"])

    # Create the table header with the fields
    table_header = ['No.', 'lastUpdatedTime', 'severity', 'comment', 'message']
    table = PrettyTable(table_header)
    table.align["lastUpdatedTime"] = "l"
    table.align["severity"] = "l"
    table.align["comment"] = "l"
    table.align["message"] = "l"

    if number_of_alerts_notices > number_of_items_to_display_on_bot:
        items = alerts_notices["items"]
        for count in range(0,number_of_items_to_display_on_bot):
            row = [str(count+1), items[count]["lastUpdatedTime"], items[count]["severity"], items[count]["comment"], items[count]["message"]]
            table.add_row(row)

    elif number_of_alerts_notices > 0 and number_of_alerts_notices < number_of_items_to_display_on_bot:
        items = alerts_notices["items"]
        for count in range(0, number_of_alerts_notices):
            row = [str(count+1), items[count]["lastUpdatedTime"], items[count]["severity"], items[count]["comment"], items[count]["message"]]
            table.add_row(row)

    elif number_of_alerts_notices == 0:
        print_info("No Inbox-ed Alerts present")

    # Return the table
    return table

def get_snapshot(vmstore,session_id):
    # Get snapshot info
    url = "/v310/snapshot"
    ret = get_info(vmstore, session_id, url)

    return ret

def create_snapshot_table(snapshot_notices):
    # Number of items to display within bot
    number_of_items_to_display_on_bot = 20

    # get the total number of snapshots
    number_of_snapshot_notices = int(snapshot_notices["filteredTotal"])

    # Create the table header with nesessary fields
    table_header = ['No.', 'lastUpdatedTime', 'vmName', 'description', 'sizeChangedMB', 'sizeChangedPhysicalMB']
    table = PrettyTable(table_header)
    table.align["lastUpdatedTime"] = "l"
    table.align["VM-Name"] = "l"
    table.align["description"] = "l"
    table.align["sizeChangedMB"] = "l"
    table.align["sizeChangedPhysicalMB"] = "l"

    if number_of_snapshot_notices > number_of_items_to_display_on_bot:
        items = snapshot_notices["items"]
        for count in range(0,number_of_items_to_display_on_bot):
            row = [str(count+1), items[count]["lastUpdatedTime"], items[count]["vmName"], items[count]["description"], items[count]["sizeChangedMB"], items[count]["sizeChangedPhysicalMB"]]
            table.add_row(row)

    elif number_of_snapshot_notices > 0 and number_of_snapshot_notices < number_of_items_to_display_on_bot:
        items = snapshot_notices["items"]
        for count in range(0, number_of_snapshot_notices):
            row = [str(count+1), items[count]["lastUpdatedTime"], items[count]["vmName"], items[count]["description"], items[count]["sizeChangedMB"], items[count]["sizeChangedPhysicalMB"]]
            table.add_row(row)

    elif number_of_snapshot_notices == 0:
        print_info("No Snapshots present")

    # Return the table
    return table
