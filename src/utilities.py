import json

def readExperimentConfiguration(configFilePath):
    configFilePath = configFilePath
    print("configFilePath: ",configFilePath)
    print("reading experiment config")
    with open(configFilePath,"r") as configFile:
        experimentConfig = json.load(configFile)
    return experimentConfig

def writeCostToFile(burCost, onDemandCost)
    with open("costs.csv", "w") as costFile:
        costFile.write("Instance Id, Instance Type, Total Cost\n")
        for instanceId, cost in burCost.items():
            costFile.write(f"{instanceId}, {burCost[instanceId]['InstanceType']}, {cost}\n")
        for instanceId, cost in onDemandCost.items():
            costFile.write(f"{instanceId}, {onDemandCost[instanceId]['InstanceType']}, {cost}\n")