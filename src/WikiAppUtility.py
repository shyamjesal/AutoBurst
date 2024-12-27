import json
import subprocess
from shutil import copyfile
import os

import Variables as Var
import InstanceUtility as InstanceUtility

def updateOldStringWithNewStringInLocalSettings(oldString, newString):
    fin = open(Var.localSettingsTemp, "r")
    data = fin.read()
    data = data.replace(oldString, newString)
    fin.close()
    fout = open(Var.localSettingsTemp, "w")
    fout.write(data)
    fout.close()
    return


def createTemp(source, destination):
    copyfile(src=source, dst=destination)
    return

def setDbIpInLocalSettings(dbIP):
    localSettingsCurrentDbString = '$wgDBserver = "' + str(dbIP) + '";'
    updateOldStringWithNewStringInLocalSettings(oldString=Var.localSettingsDefaultDbString,
                                                newString=localSettingsCurrentDbString)
    return

def changeServerIpInLocalSettings(serverIP):
    localSettingsCurrentServerString = '$wgServer="http://' + str(serverIP) + '";'
    updateOldStringWithNewStringInLocalSettings(oldString=Var.localSettingsDefaultServerString,
                                                newString=localSettingsCurrentServerString)

    return

def changeMemcacheDIpInLocalSettings(memcachedIP):
    localSettingsCurrentMemcachedString = '$wgMemCachedServers=["' + str(memcachedIP) + '"];'
    updateOldStringWithNewStringInLocalSettings(oldString=Var.localSettingsDefaultMemcachedString,
                                                newString=localSettingsCurrentMemcachedString)

    return

def sendFilesToWikiVm(wikiVmInfo, remoteFilepath, filename):
    wikiVmInfoRetrieved = InstanceUtility.findInstanceByInstanceID(wikiVmInfo["InstanceId"])
    print(wikiVmInfoRetrieved)
    remotePath = 'ubuntu@' + wikiVmInfoRetrieved["PrivateIPs"] + ':' + remoteFilepath

    cmd = ['scp', '-i', Var.key, filename, remotePath]
    info = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')

    return

# Update both database IP and load balancer IP in localSettings file of all wikimedia nodes
def updateLocalSettingsAll(dbIP, dbCount, allWikiNodeInfo, loadBalancerIP, cacheIP, cacheCount):
    i = 0
    for wikiNodeInfo in allWikiNodeInfo["Instances"]:
        wikiNodeId = wikiNodeInfo["InstanceId"]
        createTemp(Var.localSettingsSource, Var.localSettingsTemp)

        setDbIpInLocalSettings(dbIP=dbIP[i % dbCount])
        changeServerIpInLocalSettings(serverIP=loadBalancerIP)

        if cacheCount == 0:
            changeMemcacheDIpInLocalSettings(memcachedIP=cacheIP[0])
        else:
            changeMemcacheDIpInLocalSettings(memcachedIP=cacheIP[i % cacheCount])

        i = i + 1

        sendFilesToWikiVm(wikiVmInfo=wikiNodeInfo, remoteFilepath=Var.localSettingsDestination,
                          filename=Var.localSettingsTemp)
        InstanceUtility.executeCommandInInstance(instanceID=wikiNodeId, commandString='sudo service apache2 restart')
    return
