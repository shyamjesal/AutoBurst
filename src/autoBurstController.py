# from threading import Thread
from threading import Lock,Thread
import utilities
import Variables as Var
import Node as Node
import NodeStarter as NodeStarter
import ClientAppUtility as ClientAppUtility
import LoadBalancerUtility as LoadBalancerUtility
import InstanceUtility as InstanceUtility
import WikiAppUtility as WikiAppUtility
import autoBurst as autoBurst
import time
import argparse
import datetime
import logging
import subprocess
logger = logging.getLogger(__name__)

# `curr_onD`: Tracks currently running on-demand instances
curr_onD = []
onD = []
# `curr_bur`: Tracks currently running burstable instances
curr_bur = []
bur = []
# `stopped_instances_pending`: Tracks burstable instances pending termination and uses this information to use up their credits
stopped_instances_pending = []
# `stopped_instances`: Tracks instances pending termination
stopped_instances = []

allBurstables = []

# Set client running and thread running flags
# These should be boolean flags controlling the experiment flow
clientRunning = True
shortTermThreadRunning = True

burCost = {}
ondCost = {}

def runClient(config, Var):
    global clientRunning
    ## run client
    ClientAppUtility.startClient(config, Var)
    clientRunning = False

def shortTermDecision(lock, autoburst, onD, bur, pending_stop, Var, expectedDuration):
    while clientRunning:
        startTime = time.time()
        ## Collect latency stats in the format: latency (list): A list containing the latency measurements (in nanoseconds). Only the first value is used.
        latency = ClientAppUtility.getLatencyStatsK6Cloud(Var)
        logger.info(f"Latency stats: {latency}")
        with lock:
            autoburst.latency_optimizer(bur, latency, pending_stop)
            # Update load balancer with the updated weights from latency_optimizer
            LoadBalancerUtility.updateConf(onD, bur, pending_stop)
        endTime = time.time()
        duration = endTime - startTime
        if duration < expectedDuration:
            sleepTime = expectedDuration - duration
            time.sleep(sleepTime)
    global shortTermThreadRunning
    shortTermThreadRunning = False

def getWikiNodeInfo(wikiNodeInfo):
    '''setupInitialNodes created the wikiNodes'''
    for wiki in wikiNodeInfo["Instances"]:
        if wiki["InstanceType"].startswith("t"):
            if wiki["InstanceType"].startswith("t2"):
                bur.append(Node.Node(wiki, 1, 60))
            elif wiki["InstanceType"].startswith("t3"):
                bur.append(Node.Node(wiki, 1))
            elif wiki["InstanceType"].startswith("t4"):
                bur.append(Node.Node(wiki, 1))
            allBurstables.append(wiki["InstanceId"])
        else:
            onD.append(Node.Node(wiki, 1))

def setStartUpNodes(lock, init_od=1, init_bur=1):

    for instance in bur:
        burCost[instance.info["InstanceId"]] = []
    for instance in onD:
        ondCost[instance.info["InstanceId"]] = []

    with lock:
        for i in range(init_od):
            curr_onD.append(onD.pop(0))
        for i in range(init_bur):
            curr_bur.append(bur.pop(0))

    # stop the running instances in onD and bur
    stopped_instances_list = []
    for instance in onD:
        InstanceUtility.stopInstanceNonBlocking(instance.info)
        stopped_instances_list.append(instance)
    for instance in bur:
        InstanceUtility.stopInstanceNonBlocking(instance.info)
        stopped_instances_list.append(instance)
    # block until all instances stopped
    for instance in stopped_instances_list:
        InstanceUtility.block(instance.info, 'stopped')

def setupInitialNodes(Var=Var):
    # start the load balancer
    loadBalancerInfo = NodeStarter.startLoadBalancerNode(Var.LB_INSTANCE_ID)

    # start the client
    clientStartInfo = NodeStarter.startClientNode(Var.clientInstanceID)

    # # start the db
    dbStartInfo = {}
    dbBaseInfo = {}

    for i in range(0, Var.DBcount):
        dbBaseInfo[i] = Var.DB_INSTANCE_LIST[i]
        dbStartInfo[i] = NodeStarter.startDBNode(dbBaseInfo[i])

    # start onD nodes
    wikiCreationInfo = NodeStarter.createWikiNode(wikiIndex="", vmCount=Var.fixedWikiNodesCountOnD,
                                                  Var=Var, imageID=Var.WIKI_OND_IMAGE_ID, vmType=Var.WIKI_OND_VM_TYPE)
    # start burstable nodes
    wikiCreationInfobur = NodeStarter.createWikiNode(wikiIndex="", vmCount=Var.fixedWikiNodesCountBur,
                                                     Var=Var, imageID=Var.WIKI_BUR_IMAGE_ID,
                                                     vmType=Var.WIKI_BUR_VM_TYPE)

    wikiCreationInfo["Instances"] = wikiCreationInfo["Instances"] + wikiCreationInfobur["Instances"]
    time.sleep(Var.sleepAfterNodeStartInSeconds)

    lbInfo = InstanceUtility.findInstanceByInstanceID(Var.LB_INSTANCE_ID)

    dbInfo = {}
    dbIP = {}
    for i in range(0, Var.DBcount):
        dbInfo[i] = InstanceUtility.findInstanceByInstanceID(dbBaseInfo[i]["InstanceId"])
        dbIP[i] = dbInfo[i]["PrivateIPs"]  # convert to private

    dbAttachTracker = WikiAppUtility.startHelloAll(dbIP=dbIP, dbCount=Var.DBcount, allWikiNodeInfo=wikiCreationInfo,
                                                            loadBalancerIP=lbInfo["PrivateIPs"], cacheIP=["127.0.0.1:11211"], cacheCount= 0)
    
    
    LoadBalancerUtility.setupIntialNginxConf(wikiCreationInfo=wikiCreationInfo, Var=Var)

    initialNodeInfo = {}

    initialNodeInfo["dbStartInfo"] = dbStartInfo
    initialNodeInfo["wikiCreationInfo"] = wikiCreationInfo
    initialNodeInfo["clientStartInfo"] = clientStartInfo
    initialNodeInfo["loadBalancerInfo"] = loadBalancerInfo
    # initialNodeInfo["IPinfo"] = IPinfo

    return initialNodeInfo


def runExperiments(configFilePath):

    experimentConfig = utilities.readExperimentConfiguration(configFilePath=configFilePath)
    config = experimentConfig[0]

    lock = Lock()

    nodeInfo = setupInitialNodes(Var=Var)

    wikiCreationInfo = nodeInfo["wikiCreationInfo"]
    getWikiNodeInfo(nodeInfo["wikiCreationInfo"])

    # Start instances and initialize everything including curr_onD and curr_bur lists

    autoburst = autoBurst.AutoBurstPolicies(config["H"], config["L"], config["onDnodes"], config["burNodes"], config["meanSLO"], config["P"], config["D"], config["throughputfilename"], config["potentialIncreaseFactor"], config["desiredLoad"], config["P_m"], config["D_m"], config["desiredCredit"])

    onD_init_count = config["onDnodes"]
    bur_init_count = config["burNodes"]
    setStartUpNodes(lock, onD_init_count, bur_init_count)

    with lock:
        autoburst.init_weight(curr_onD, curr_bur, config["init_weight"])
        LoadBalancerUtility.updateConf(curr_onD, curr_bur, pending_stop=[])

    # Sleep for a while to earn credits in seconds
    if "creditEarnDuration" in config:
        time.sleep(config["creditEarnDuration"])

    # startClient in separate thread
    Thread(target=runClient, args=(config, Var)).start()

    # startTimeForArrRate = ClientAppUtility.waitForWarmUp(Var)
    startTimeForArrRate = time.time()
    prevReqs = LoadBalancerUtility.getNumberOfReqs(Var)
    # arrRate = LoadBalancerUtility.getArrivalRate(Var, duration=1)
    # start shortTermDecision in a separate thread
    Thread(target=shortTermDecision, args=(lock, autoburst, curr_onD, curr_bur, stopped_instances_pending, Var, config["durationLE"])).start()

    # cost calculation update
    for instance in curr_bur:
        burCost[instance.info["InstanceId"]].append([datetime.datetime.now(), 0])
    for instance in curr_onD:
        ondCost[instance.info["InstanceId"]].append([datetime.datetime.now(), 0])

    while (clientRunning):
        loopTimeStart = time.time()

        # Stopping burstable instances
        # If credit 0 then stop, else keep running. for stopping, move to stopped instance list
        lenStopped = len(stopped_instances_pending)
        j = 0
        for i in range(0, lenStopped):
            print("Check credit of instance")
            credit = InstanceUtility.getMetricStats(stopped_instances_pending[j].info["InstanceId"], "Average", "CPUCreditBalance")[0]
            if credit < 0.1:
                with lock:
                    stopped_instances.append(stopped_instances_pending.pop(j))
            else:
                j += 1

        # Stopping for onDemand instances
        # Stopping all instances in stopped_instances, waiting until all of them done. Then moving them.
        lenStopped = len(stopped_instances)
        for i in range(0, lenStopped):
            InstanceUtility.stopInstanceNonBlocking(stopped_instances[i].info)

        for i in range(0, lenStopped):
            InstanceUtility.block(stopped_instances[i].info, 'stopped')

        for i in range(0, lenStopped):
            if stopped_instances[0].info["InstanceType"].startswith("t"):
                # cost calculation update
                if len(burCost[stopped_instances[0].info["InstanceId"]]) < 1:
                    temp = [0, 0]
                else:
                    temp = burCost[stopped_instances[0].info["InstanceId"]].pop()
                temp[1] = datetime.datetime.now()
                burCost[stopped_instances[0].info["InstanceId"]].append(temp)

                # actual appending and pop
                bur.append(stopped_instances.pop(0))

            else:
                # cost calculation update
                if len(ondCost[stopped_instances[0].info["InstanceId"]]) < 1:
                    temp = [0, 0]
                else:
                    temp = ondCost[stopped_instances[0].info["InstanceId"]].pop()
                temp[1] = datetime.datetime.now()
                ondCost[stopped_instances[0].info["InstanceId"]].append(temp)

                # actual appending and pop
                onD.append(stopped_instances.pop(0))


        endTimeForArrRate = time.time()
        duration = endTimeForArrRate - startTimeForArrRate
        # Write code to get number of requests from the LoadBalancer
        currReqs = LoadBalancerUtility.getNumberOfReqs(Var)
        reqs = currReqs - prevReqs - 1  # removing the extra reqs by curl in this duration
        arrRate = reqs / duration
        prevReqs = currReqs
        startTimeForArrRate = time.time()

        logger.info(f"Current OnD instances: {len(curr_onD)}, Current Burstable instances: {len(curr_bur)}, Stopped instances pending: {len(stopped_instances_pending)}")
        od, b = autoburst.resource_estimator(arrRate, bur=curr_bur,
                                                           stop_pending=stopped_instances_pending, onD=len(curr_onD), unused_onD = len(onD))
        logger.info(f"Estimated OnD instances: {od}, Estimated Burstable instances: {b}")

        # Write code to start extra onD instances and to stop extra onD instances
        if (od > len(curr_onD)):
            # start extra nodes. update curr_od
            countAddedInst = 0
            with lock:
                while (od > len(curr_onD)):
                    if len(onD) > 0:
                        InstanceUtility.startInstance(onD[0].info)
                        if len(curr_onD) > 0:
                            onD[0].weight = curr_onD[0].weight
                        else:
                            onD[0].weight = 1

                        # cost calculation update
                        if onD[0].info["InstanceId"] not in ondCost.keys():
                            print("Problem: onD instance not in cost list")
                        ondCost[onD[0].info["InstanceId"]].append([datetime.datetime.now(), 0])

                        curr_onD.append(onD.pop(0))
                        countAddedInst = countAddedInst + 1


                    else:
                        # no more available onD
                        break

            # block until all instances started
            for i in range((len(curr_onD) - countAddedInst), len(curr_onD)):
                InstanceUtility.block(curr_onD[i].info, 'running')
        elif (od < len(curr_onD)):
            # stop extra nodes onD
            with lock:
                while od < len(curr_onD):
                    stopped_instances.append(curr_onD.pop(0))

        if (b > len(curr_bur)):
            #  start extra nodes. update curr_bur
            countAddedInst = 0

            with lock:
                for instance in stopped_instances_pending:
                    instance.creditBalance = InstanceUtility.getCredit(instance.info["InstanceId"], "Average")[
                        0]

                # sort descending based on creditBalance
                stopped_instances_pending.sort(key=lambda x: x.creditBalance, reverse=True)

                while b > len(curr_bur):
                    if len(stopped_instances_pending) > 0:
                        stopped_instances_pending[0].weight = config["L"]
                        curr_bur.append(stopped_instances_pending.pop(0))
                        countAddedInst = countAddedInst + 1
                    elif len(bur) > 0:
                        InstanceUtility.startInstance(bur[0].info)
                        bur[0].weight = config["L"]
                        # cost calculation update
                        if bur[0].info["InstanceId"] not in burCost.keys():
                            print("Problem: bur instance not in cost list")
                        burCost[bur[0].info["InstanceId"]].append([datetime.datetime.now(), 0])

                        curr_bur.append(bur.pop(0))
                        countAddedInst = countAddedInst + 1
                    else:
                        # no more available burstables
                        break

            # block until all instances start running
            for i in range((len(curr_bur) - countAddedInst), len(curr_bur)):
                InstanceUtility.block(curr_bur[i].info, 'running')

        # Put burstable instances to be stopped in stopped_pending lists, to be stopped once they run out of credit
        elif (b < len(curr_bur)):
            # remove len(curr_bur)-b nodes from list based on credit level, add to removed_instances
            # update credit level for each instance
            # stop extra node
            with lock:
                for instance in curr_bur:
                    instance.creditBalance = InstanceUtility.getCredit(instance.info["InstanceId"], "Average")[0]
            # sort ascending based on creditBalance
            curr_bur.sort(key=lambda x: x.creditBalance)
            with lock:
                while len(curr_bur) > b and len(curr_bur) > 0:
                    instanceToDrain = curr_bur.pop(0)
                    stopped_instances_pending.append(instanceToDrain)

        loopTimeEnd = time.time()
        loopDur = loopTimeEnd-loopTimeStart
        if loopDur < config["durationRE"]:
            time.sleep(config["durationRE"]-loopDur)
            logger.info(f"Sleeping for {config['durationRE'] - loopDur} seconds to maintain the loop duration.")
            
    while (shortTermThreadRunning):
        time.sleep(1)

    # Write code to stop/terminate all instances
    InstanceUtility.stopAllRunningInstances(instanceInfo=nodeInfo)
    InstanceUtility.deleteInstances(instanceInfos=nodeInfo["wikiCreationInfo"])

    # cost calculation: instance stop time
    for k in burCost.keys():
        # print(len(burCost[k]))
        if len(burCost[k]) > 0:
            if burCost[k][-1][1] == 0:
                temp = burCost[k].pop()
                temp[1] = (datetime.datetime.now())
                burCost[k].append(temp)
    for k in ondCost.keys():
        if len(ondCost[k]) > 0:
            if ondCost[k][-1][1] == 0:
                temp = ondCost[k].pop()
                temp[1] = (datetime.datetime.now())
                ondCost[k].append(temp)

    # Write code to write the cost to a file
    utilities.writeCostToFile(burCost, ondCost)

def main():
    logging.basicConfig(level=logging.INFO)
    # remove rm /home/ubuntu/.ssh/known_hosts
    subprocess.run(['rm', '/home/ubuntu/.ssh/known_hosts'])
    my_parser = argparse.ArgumentParser(allow_abbrev=False, description='Run AutoBurst with config file path')

    my_parser.add_argument("--configFile", action='store', type=str, required=True, metavar='Required: path of the config file')

    args = my_parser.parse_args()
    configFilePath = args.configFile

    runExperiments(configFilePath)

if __name__ == '__main__':
    main()
