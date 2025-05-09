
#pem file path
key = '/home/ubuntu/.ssh/aws-shyam.pem'

keyName = "aws-shyam"
WIKI_keyName = "aws-shyam"
securityGroup = "launch-wizard-18"
# placement = "{\"GroupId\": \"pg-06ba00dcbf1293ac7\"}"
placement = "{}"

# db info
DB_INSTANCE_PREFIX = "mysql"
DB_IMAGE_NAME = "mysql-image"
dbPort = 3306
DB_INSTANCE_LIST = [{"instanceName": "mysql-1", "InstanceId": "i-0fc042a0cbeb3017c"}]
DBcount = 1


# wiki info
WIKI_INSTANCE_PREFIX = "wiki"
WIKI_securityGroup = "launch-wizard-18"
# WIKI_placement = "{\"GroupId\": \"pg-06ba00dcbf1293ac7\"}"
WIKI_placement = "{}"
WIKI_monitoring = "Enabled=true"
wikiPort = 80
startWikiIndex = 1
localSettingsDestination = "/var/www/html/LocalSettings.php"


WIKI_OND_IMAGE_ID = "ami-054c232b54f3bf58d"
WIKI_OND_VM_TYPE = "m5.large"

WIKI_BUR_IMAGE_ID =  "ami-054c232b54f3bf58d"
WIKI_BUR_VM_TYPE = "t3.large"

# { instanceType : (vcpu, baseline)}
burstable_vcpu_baseline = {"t2.large": (2, 0.3), "t4g.large": (2, 0.3), "t3.large": (2, 0.3), "t3.small": (2, 0.2)}


# load balancer info
LB_INSTANCE_PREFIX = "autoBurst-LB"
LB_INSTANCE_ID = "i-05956d3831e8f4f25"
loadBalancerPrivateIP = "172.31.40.151"
loadBalancerPublicIP = "35.88.99.34"

wikiConfigDestination = "/etc/nginx/conf.d/wiki-config.conf"
wikiConfigSource = "wiki-config_base.conf"
wikiConfigTemp = "wiki-config_base_temp.conf"
loadBalancerInstanceName = "autoBurst-LB-1"

# client info
# clientCheckPort =
clientPrivateIP = "172.31.33.255"
clientJarAddress = "/home/ubuntu/traceReplay.jar"
maxClientMemory = "-Xmx4096M"
clientInstanceName = "autoBurst-client"
clientInstanceID = "i-081cb76144c730dd1"

# controller info
localSettingsSource = "LocalSettings_base.php"
localSettingsTemp = "LocalSettings_temp.php"
localSettingsDefaultServerString = '$wgServer="http://0.0.0.0";'
localSettingsDefaultDbString = '$wgDBserver = "";'
localSettingsDefaultMemcachedString = '$wgMemCachedServers = [""];'

# experiment info
resultDirPathClient = ""
clientBaseConfig = "config/base_config.json"
tempClientConfig = "config/base_config_temp.json"
finalClientConfig = "/path/config.json"
resultStorageDirectory = "/home/ubuntu/results"
clientStatusCheckIntervalInSeconds = 2.0
fixedWikiNodesCountOnD = 5
fixedWikiNodesCountBur = 5
sleepAfterNodeStartInSeconds=120
sleepAfterUpdatingNginxConfInSeconds=60
