import json

def readExperimentConfiguration(configFilePath):
    configFilePath = configFilePath
    print("configFilePath: ",configFilePath)
    print("reading experiment config")
    with open(configFilePath,"r") as configFile:
        experimentConfig = json.load(configFile)
    return experimentConfig
