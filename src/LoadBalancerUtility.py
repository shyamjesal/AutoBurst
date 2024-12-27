import subprocess

import Variables as Var
from nginxParser import load, dump
import InstanceUtility as InstanceUtility
from shutil import copyfile

prevReqs = 0
prevIpWeight = []


def createTempLocalWikiConfig(Var):
    copyfile(src=Var.wikiConfigSource, dst=Var.wikiConfigTemp)
    return

def initializeNginxConf(serverIpList, Var):
    with open(Var.wikiConfigTemp, "r") as inputFile:
        content = load(inputFile)
    lbPolicy = content[1][1][0]
    content[1][1].clear()
    content[1][1].append(lbPolicy)
    for ip, weight in serverIpList:
        newServer = ['server']
        newServer.append(str(ip) + ":" + str(Var.wikiPort) + " weight=" + str(weight))
        content[1][1].append(newServer)
    with open(Var.wikiConfigTemp, "w") as outputFile:
        dump(content, outputFile)
    return

def sendUpdatedNginxConf(Var):
    remotePath = 'ubuntu@' + Var.loadBalancerPrivateIP + ':' + Var.wikiConfigDestination

    cmd = ['scp', '-i', Var.key, Var.wikiConfigTemp, remotePath]

    info = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')

    return

def reloadNginxLB(Var):
    commandString = 'sudo service nginx reload'
    InstanceUtility.executeCommandInInstance(instanceID=Var.LB_INSTANCE_ID, commandString=commandString)
    return

def setupIntialNginxConf(wikiCreationInfo, Var):

    wikiIps = [(x['PrivateIpAddress'], 1) for x in wikiCreationInfo["Instances"]]
    if not wikiIps:
        print("Nothing to add to LB")
        return
    createTempLocalWikiConfig(Var=Var)
    initializeNginxConf(serverIpList=wikiIps, Var=Var)
    sendUpdatedNginxConf(Var=Var)
    commandString = 'sudo service nginx restart'
    InstanceUtility.executeCommandInInstance(instanceID=Var.LB_INSTANCE_ID, commandString=commandString)
    reloadNginxLB(Var)
    return

def updateConf(curr_onD, curr_bur, pending_stop):
    ipWeight = [(x.info['PrivateIpAddress'], x.weight) for x in curr_onD]
    ipWeight += [(x.info['PrivateIpAddress'], x.weight) for x in curr_bur]
    ipWeight += [(x.info['PrivateIpAddress'], x.weight) for x in pending_stop]
    global prevIpWeight
    if not prevIpWeight or not (len(ipWeight) == len(prevIpWeight) and len(ipWeight) == sum(
            [1 for i, j in zip(ipWeight, prevIpWeight) if i == j])):
        initializeNginxConf(ipWeight, Var)
        sendUpdatedNginxConf(Var=Var)
        reloadNginxLB(Var)
    prevIpWeight = ipWeight