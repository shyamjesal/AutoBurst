import InstanceUtility as InstanceUtility


##This file is wrapper around InstanceUtility

def startLoadBalancerNode(instanceID):
    loadBalancerInfo = {"instanceName": "LB", "InstanceId": instanceID}
    loadBalancerStartInfo = InstanceUtility.startInstance(instanceInfo=loadBalancerInfo)
    return loadBalancerStartInfo

def startClientNode(instanceID):
    clientStartInfo = {"instanceName": "client", "InstanceId": instanceID}
    clientStartInfo = InstanceUtility.startInstance(instanceInfo=clientStartInfo)
    return clientStartInfo

def startDBNode(dbInstanceInfo):
    dbStartInfo = InstanceUtility.startInstance(instanceInfo=dbInstanceInfo)

    return dbStartInfo


def createWikiNode(wikiIndex, vmCount, Var, imageID, vmType):
    if(vmCount==0):
        return {'Groups': [],'Instances': [], 'OwnerId': '', 'ReservationId': ''}
    instanceNamePrefix = Var.WIKI_INSTANCE_PREFIX + str(wikiIndex)
    wikiCreationInfo = {"instanceName": instanceNamePrefix,
                        "imageID": imageID,
                        "vmCount": vmCount,
                        "instanceType": vmType,
                        "keyName": Var.WIKI_keyName,
                        "securityGroup": Var.WIKI_securityGroup,
                        "placement": Var.WIKI_placement,
                        "monitoring": Var.WIKI_monitoring}
    wikiStartInfo = InstanceUtility.createInstanceFromImage(imageCreationInfo=wikiCreationInfo)
    return wikiStartInfo