import subprocess
commandString = ['bash', './k6get.sh' ,"|", "jq", '".[1]"']
    # remoteServer = 'ubuntu@' + Var.clientPrivateIP
    # cmd = ['ssh', '-i', Var.key, remoteServer, commandString]

info = subprocess.run(commandString, stdout=subprocess.PIPE).stdout.decode('utf-8')
print(info.split())