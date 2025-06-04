import subprocess

import Variables as Var
from nginxParser import load, dump
import InstanceUtility as InstanceUtility
from shutil import copyfile
import time
import logging
logger = logging.getLogger(__name__)

prevReqs = 0
prevIpWeight = []


def getArrivalRate(Var, duration=1):
    """
    Get the arrival rate of requests to the NGINX load balancer.

    Args:
        Var: Variables module containing configuration values
        duration (int): Duration in seconds for which to calculate the arrival rate

    Returns:
        float: The arrival rate of requests per second
    """
    global prevReqs

    # Get the current number of requests processed by the load balancer
    currReqs = getNumberOfReqs(Var)

    if currReqs == 0:
        print("No requests processed by load balancer")
        return 0
    # If this is the first call, set the previous request count to the current count
    if prevReqs == 0:
        prevReqs = currReqs
    
    time.sleep(duration)
    # Get the current number of requests again
    currReqs = getNumberOfReqs(Var)
    if currReqs == 0:
        print("No requests processed by load balancer")
        return 0

    # Calculate the arrival rate
    arrivalRate = (currReqs - prevReqs) / duration

    # Update the previous request count
    prevReqs = currReqs

    return arrivalRate


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
        logger.info(f"Current requests: {currReqs}")
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
    commandString = 'sudo rm /var/log/nginx/wikiLog_access_test.log ; sudo /usr/local/nginx/nginx'
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
