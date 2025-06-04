import subprocess
import time
import json
import pipes
import LoadBalancerUtility

def waitForWarmUp(Var):
    remoteServer = 'ubuntu@' + Var.clientPrivateIP
    path = '/path/signal.txt'
    commandString = 'test -e {}'.format(pipes.quote(path))
    cmd = ['ssh', '-i', Var.key, remoteServer, commandString]
    t2 = 0
    while (subprocess.call(cmd) == 1):
        t1 = time.time()
        LoadBalancerUtility.getArrivalRate(Var, duration=1)
        t2 = time.time()
        diff = t2 - t1
        if diff < 1:
            time.sleep(1 - diff)
    return t2

def startClient(config, Var):
    # sendUpdatedPropertiesFileToClient(config, Var)
    runTraceReplayerBlocking(Var)
    return

def sendUpdatedPropertiesFileToClient(config, Var):
    createTempPropertiesFile(config=config, Var=Var)

    fileSendCommand = ["scp","-i"]
    fileSendCommand.extend([Var.key])
    fileSendCommand.extend([Var.tempClientConfig])
    targetFilePath = 'ubuntu@' + Var.clientPrivateIP + ':' + Var.finalClientConfig
    fileSendCommand.extend([targetFilePath])
    info = subprocess.run(fileSendCommand, stdout=subprocess.PIPE).stdout.decode('utf-8')

    return


def createTempPropertiesFile(config, Var):
    with open(Var.clientBaseConfig, "r") as baseConfigFile:
        baseConfig = json.load(baseConfigFile)

    resultsDirectoryPath = Var.resultDirPathClient
    # update trace file path
    traceFileReplayAddress = config["traceFileDirectoryPath"] + "/" + config["traceFileName"]
    baseConfig["traceFileReplayAddress"] = traceFileReplayAddress

    # update request response time files
    reqResponseFileNameStart = config[resultsDirectoryPath] + "/" + config["experimentName"] + "/requestResponseTimes_"
    baseConfig["requestResponseTimeFileNameStart"] = reqResponseFileNameStart

    baseConfig["requestResponseTimeFileNameEnd"] = config["experimentName"] + baseConfig[
        "requestResponseTimeFileNameEnd"]


    # update traceline response files
    tracelineResponseFileNameStart = config[resultsDirectoryPath] + "/" + config["experimentName"] + "/tracelineResponseTimes_"
    baseConfig["traceLineResponseTimeFileNameStart"] = tracelineResponseFileNameStart

    baseConfig["traceLineResponseTimeFileNameEnd"] = config["experimentName"] + baseConfig[
        "traceLineResponseTimeFileNameEnd"]

    # update file to change LB IP
    LBIP = Var.loadBalancerPrivateIP
    dummyUrl = "-http://" + LBIP + "/index.php/Main_Page-"

    baseConfig["urlList"]["BROWSE"] = dummyUrl
    baseConfig["urlList"]["LOG_IN"] = dummyUrl
    baseConfig["urlList"]["POST_SELF_WALL"] = dummyUrl
    baseConfig["dummyUrl"] = dummyUrl

    combinedConfig = {**baseConfig, **config}
    with open(Var.tempClientConfig, "w") as outfile:
        json.dump(combinedConfig, outfile)

    return


def runTraceReplayerBlocking(Var):

    # Kill any existing k6 processes
    killCommand = ['ssh', '-i', Var.key, 'ubuntu@' + Var.clientPrivateIP, 'pkill -f k6']
    subprocess.call(killCommand)

    # remove old results file
    removeCommand = ['ssh', '-i', Var.key, 'ubuntu@' + Var.clientPrivateIP, 'rm -f /home/ubuntu/load_results.json']
    subprocess.call(removeCommand)

    cmd = ['ssh','-i',Var.key]
    cmd.extend(['ubuntu' + '@' + Var.clientPrivateIP])
    cmd.extend(['/home/ubuntu/k6'])
    cmd.extend(['cloud' ,'run', '--local-execution'])
    client_string = 'MY_CLIENT="http://' + Var.loadBalancerPrivateIP +'"'
    cmd.extend(['--env', client_string])
    # cmd.extend(['--out', 'json=/home/ubuntu/load_results.json'])
    cmd.extend(['/home/ubuntu/load.js', "--quiet"])

    cmdString = ' '.join(cmd)

    subprocess.call(cmd)
    time.sleep(15)
    return


def getLatencyStats(Var):
    commandString = 'tail -n 200 /home/ubuntu/load_results.json | jq -s \' [ .[] | select(.type == "Point" and .metric == "http_req_duration" and (.data.tags.status | tonumber) >= 200) ] \
        | map(.data.value) \
        | sort \
        | if length > 0 then \
            (length - 1) as $len | \
            (0.95 * $len | floor) as $index | \
            .[$index] \
            else \
            "Insufficient data" | halt_error(1) \
            end \
        \''
    remoteServer = 'ubuntu@' + Var.clientPrivateIP
    cmd = ['ssh', '-i', Var.key, remoteServer, commandString]

    info = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    return info.split()

def getLatencyStatsK6Cloud(Var):
    commandString = ['bash', './k6get.sh' ,"|", "jq", '".[1]"']
    # remoteServer = 'ubuntu@' + Var.clientPrivateIP
    # cmd = ['ssh', '-i', Var.key, remoteServer, commandString]

    info = subprocess.run(commandString, stdout=subprocess.PIPE).stdout.decode('utf-8')
    while info == 'null\n':
        info = subprocess.run(commandString, stdout=subprocess.PIPE).stdout.decode('utf-8')
        
    return info.strip()