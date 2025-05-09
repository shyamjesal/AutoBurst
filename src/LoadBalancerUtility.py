import subprocess

import Variables as Var
from nginxParser import load, dump
import InstanceUtility as InstanceUtility
from shutil import copyfile

prevReqs = 0
prevIpWeight = []

def getNumberOfReqs(Var):
    """
    Get the number of requests processed by the NGINX load balancer.

    Args:
        Var: Variables module containing configuration values

    Returns:
        int: The total number of requests processed by the load balancer
    """
    global prevReqs

    # Command to get request stats from NGINX status page
    commandString = 'curl -s http://localhost/nginx_status | awk \'NR==3 {print $3}\''

    # Execute command on the load balancer instance
    result = InstanceUtility.executeCommandInInstance(
        instanceID=Var.LB_INSTANCE_ID,
        commandString=commandString
    )

    try:
        # Parse the result to get the number of requests
        currReqs = int(result.strip())
        return currReqs
    except (ValueError, AttributeError):
        # If there was an error parsing the result, return the previous count
        print("Error getting request count from load balancer")
        return prevReqs

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
    commandString = 'sudo /usr/local/nginx/nginx -s reload'
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
    commandString = 'sudo /usr/local/nginx/nginx'
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
