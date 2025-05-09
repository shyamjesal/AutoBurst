import datetime
import json
import subprocess
import time
import re
import Variables as Var


def findInstanceByInstanceID(instanceID):
    filter = "Name=instance-id,Values=" + instanceID
    query = 'Reservations[*].Instances[*].{instanceID:InstanceId,instanceName:Tags[?Key==`Name`]|[0].Value,PrivateIPs:PrivateIpAddress,PublicIPs:PublicIpAddress,Type:InstanceType, PublicDNS:PublicDnsName, PrivateDNS:PrivateDnsName, Status:State}'

    cmd = ['aws', 'ec2', 'describe-instances', '--filters', filter, '--query', query, '--output', 'json']

    info = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    info = json.loads(info)
    if (len(info) > 1):
        print("Error in finsInstanceByName: more than 1 instances match the name")
        return -1
    return info

def executeCommandInInstance(instanceID, commandString):
    instance = findInstanceByInstanceID(instanceID)
    if instance == -1:
        raise ValueError(f"No instance found with ID {instanceID}")
    remoteServer = 'ubuntu@' + instance["PrivateIPs"]
    cmd = ['ssh', '-i', Var.key, remoteServer, commandString]
    info = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    return

''' get metric from AWS cloudwatch
    metricName can be: CPUCreditUsage, CPUCreditBalance, CPUSurplusCreditBalance, CPUSurplusCreditsCharged, CPUUtilization
    stat can be: Minimum, Maximum, Sum, Average, SampleCount, pNN.NN
    returns a tuple (stat, timestamp)'''
def getMetricStats(instanceID, stat, metricName):
    instance = "Name=InstanceId,Value=" + instanceID
    statPeriod = 60
    duration = 600
    startTime = datetime.datetime.now()- datetime.timedelta(minutes=(duration/60))
    endTime = datetime.datetime.now()
    cmd = ['aws', 'cloudwatch', 'get-metric-statistics', '--metric-name', metricName, '--start-time', str(startTime), '--end-time', str(endTime), '--period', str(statPeriod), '--namespace', 'AWS/EC2', '--statistics', stat, '--dimensions', instance]

    info = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    info = json.loads(info)
    datapoints = info["Datapoints"]

    datapoints.sort(key=lambda datapoints: datapoints["Timestamp"])

    if len(info["Datapoints"]) > 0:
        idx = len(info["Datapoints"])-1
        return (info["Datapoints"][idx][stat], info["Datapoints"][idx]["Timestamp"])
    return (-1, -1)

''' Stop instances and return immediately
    Non Blocking function to stop instance based on InstanceID in instanceInfo in AWS'''
def stopInstanceNonBlocking(instanceInfo):
    instanceID = instanceInfo["InstanceId"]
    cmd = ['aws', 'ec2', 'stop-instances', '--instance-ids', instanceID]
    subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    return

'''Blocking function to busy wait while instance state does not match target state yet based on InstanceID in instanceInfo'''
def block(instanceInfo, state):
    instanceID = instanceInfo["InstanceId"]
    a = findInstanceByInstanceID(instanceID)
    if a == -1:
        raise ValueError(f"No instance found with ID {instanceID}")
    while(a["Status"]["Name"] != state):
        time.sleep(1)
        a = findInstanceByInstanceID(instanceID)
    print(instanceID, " ", state)
    return

''' Blocking function to start instance based on InstanceID in instanceInfo
    returns instanceInfo'''
def startInstance(instanceInfo):
    instanceID = instanceInfo["InstanceId"]
    cmd = ['aws', 'ec2', 'start-instances', '--instance-ids', instanceID]
    instanceInfo = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    instanceInfo = json.loads(instanceInfo)
    return instanceInfo

''' Creates instances from image given image creation information, including an imageID'''
def createInstanceFromImage(imageCreationInfo):
    imageID = str(imageCreationInfo["imageID"])
    count = str(imageCreationInfo["vmCount"])
    type = str(imageCreationInfo["instanceType"])
    key = str(imageCreationInfo["keyName"])
    securityGroup = str(imageCreationInfo["securityGroup"])
    placement = str(imageCreationInfo["placement"])
    instanceName = str(imageCreationInfo["instanceName"])
    tag = f"ResourceType=instance,Tags=[{{Key=Name,Value={instanceName}}}]"
    cmd = ['aws', 'ec2', 'run-instances']
    cmd.extend(['--image-id', imageID])
    if str(imageCreationInfo["monitoring"]) == "Enabled=true":
        monitoring = 'Enabled=true'
        cmd.extend(['--monitoring', monitoring])
    cmd.extend(['--count', count])
    cmd.extend(['--instance-type', type])
    cmd.extend(['--key-name', key])
    cmd.extend(['--security-group-ids', securityGroup])
    cmd.extend(['--tag-specifications', tag])
    cmd.extend(['--placement', placement])
    cmdString = " ".join(cmd)
    instnaceInfo = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    # print the command string
    print(cmdString)
    instnaceInfo = json.loads(instnaceInfo)
    return instnaceInfo



'''Calculates credit from latest CPUutilization value(s). Applicable for cases when CPUutil is reported at 1 min interval but credit balance at 5 min interval'''
def getCredit(instanceID, stat):
    instance = findInstanceByInstanceID(instanceID)
    if instance == -1:
        raise ValueError(f"No instance found with ID {instanceID}")
    instanceType = instance["Type"]
    vcpu = Var.burstable_vcpu_baseline[instanceType][0]
    baseline = Var.burstable_vcpu_baseline[instanceType][1]

    latest_credit, latest_cred_ts = getMetricStats(instanceID, stat, "CPUCreditBalance")
    if (latest_credit == -1):
        return 0, 0

    latest_CPU, latest_CPU_ts_str = getMetricStatsMultiple(instanceID, stat, "CPUUtilization", latest_cred_ts)

    pattern_str1 = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}\:\d{2}$'
    pattern_str2 = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{2}$'

    latest_CPU_ts = []

    for ts in latest_CPU_ts_str:
        if re.match(pattern_str1, ts):
            latest_CPU_ts.append(datetime.datetime.strptime(ts.split("+", 1)[0], '%Y-%m-%dT%H:%M:%S'))
        elif re.match(pattern_str2, ts):
            latest_CPU_ts.append(datetime.datetime.strptime(ts.split(".", 1)[0], '%Y-%m-%dT%H:%M:%S'))


    if re.match(pattern_str1, latest_cred_ts):
        latest_cred_ts = datetime.datetime.strptime(latest_cred_ts.split("+", 1)[0], '%Y-%m-%dT%H:%M:%S')
    elif re.match(pattern_str2, latest_cred_ts):
        latest_cred_ts = datetime.datetime.strptime(latest_cred_ts.split(".", 1)[0], '%Y-%m-%dT%H:%M:%S')


    curr_credit = latest_credit
    curr_ts = latest_cred_ts

    i = 0
    for ts in latest_CPU_ts:
        diff_ts_min = (ts - curr_ts).total_seconds() / 60
        curr_credit = max(0, curr_credit + vcpu * diff_ts_min * (baseline - latest_CPU[i] / 100))
        curr_ts = ts
        i = i+1

    return (curr_credit, curr_ts)

def stopAllRunningInstances(instanceInfo):
    stopLoadBalancerServer(instanceInfo["loadBalancerInfo"])
    stopClientServer(instanceInfo["clientStartInfo"])
    stopDbServer(instanceInfo["dbStartInfo"])
    return

def stopLoadBalancerServer(loadBalancerServerInfo):
    loadBalancerInfo = {"name": "LB", "InstanceId": loadBalancerServerInfo["StartingInstances"][0]["InstanceId"]}
    stopInstanceNonBlocking(instanceInfo=loadBalancerInfo)
    return

def stopClientServer(clientServerInfo):
    clientInfo = {"name": "client", "InstanceId": clientServerInfo["StartingInstances"][0]["InstanceId"]}
    stopInstanceNonBlocking(instanceInfo=clientInfo)
    return

def stopDbServer(dbServerInfo):
    for i in range(0, Var.DBcount):
        dbStartInfo = {"name": "DB", "InstanceId": dbServerInfo[i]["StartingInstances"][0]["InstanceId"]}
        stopInstanceNonBlocking(instanceInfo=dbStartInfo)
    return

def stopInstanceNonBlocking(instanceInfo):
    '''Non Blocking function to stop instance based on InstanceID in instanceInfo'''
    instanceID = instanceInfo["InstanceId"]
    cmd = ['aws', 'ec2', 'stop-instances', '--instance-ids', instanceID]
    subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    return

def deleteInstances(instanceInfos):
    # Specific to wiki creation return type's structure from the function NodeStarter.createWikiNode
    for x in instanceInfos["Instances"]:
        instanceID = x["InstanceId"]
        cmd = ['aws', 'ec2', 'terminate-instances', '--instance-ids', instanceID]
        subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    return
