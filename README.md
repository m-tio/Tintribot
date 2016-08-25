# Tintribot
This is a bot that operaiton [Tintri](https://www.tintri.com/) VMstore storage.

##How to use.

1.Install [lins05/slackbot](https://github.com/lins05/slackbot) or`pip install slackbot`.  
2.Get the [tintri-api-examples/tintri_1_1.py](https://github.com/Tintri/tintri-api-examples).  
3.Put the tintri_1_1.py into plugins directory.  
4.Configure the API_TOKEN in the slackbot_settings.py.  
(Read https://github.com/lins05/slackbot/blob/develop/README.md.)  
5.Configure the login information and IP of the Tintri to get_VMStore_info() of the plugins/tintri_operation_v1.py.(line 45)  
```
(
  # vmstores['VMStore-Name'] = ('VMStore-IP/Name', 'VMStoreUser', 'VMStorePass')
  vmstores['tintri-001'] = ('192.168.1.x', 'admin', 'tintri')
  vmstores['tintri-002'] = ('192.168.2.x', 'admin', 'tintri')
 )
 ```

6.Run the Tintribot.py

##Usage  
 `tintri [VMStore-Name] show help`  
 First "tintri" command to respond to bot.

 Show help.  
 `tintri [VMStore-Name] show help`  

 Show appliance infomation.  
 `tintri [VMStore-Name] show appliance_info`  

 Show dashboard.  
 `tintri [VMStore-Name] show dashboard`  

 Show alerts and notices.  
 `tintri [VMStore-Name] show alert`

 Show vm list in VMStore.  
 `tintri [VMStore-Name] show vmlist`
  
 Caution!:When the number of VM is too much eliminates the response from the Slack.  

 Show vm list of [VMName] in VMStore.  
 `tintri [VMStore-Name] show vmlist search [VMName(Regular expression)]`
