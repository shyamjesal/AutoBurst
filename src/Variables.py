
#pem file path
key = ''

keyName = ""
securityGroup = ""
placement = ""

# db info
DB_INSTANCE_PREFIX = ""
DB_IMAGE_NAME = ""
dbPort = 
DB_INSTANCE_LIST = [{"instanceName": "", "InstanceId": ""},{"instanceName": "", "InstanceId": ""},{"instanceName": "", "InstanceId": ""}]
DBcount = 1


# wiki info
WIKI_INSTANCE_PREFIX = ""
WIKI_securityGroup = ""
WIKI_placement = ""
WIKI_monitoring = "Enabled=true"
wikiPort = 
startWikiIndex =
localSettingsDestination = "/var/www/html/LocalSettings.php"


WIKI_OND_IMAGE_ID = ""
WIKI_OND_VM_TYPE = "m5.large"

WIKI_BUR_IMAGE_ID =  ""
WIKI_BUR_VM_TYPE = "t3.small"

# { instanceType : (vcpu, baseline)}
burstable_vcpu_baseline = {"t2.large": (2, 0.3), "t4g.large": (2, 0.3), "t3.large": (2, 0.3), "t3.small": (2, 0.2)}


# load balancer info
LB_INSTANCE_PREFIX = ""
LB_INSTANCE_ID = "" 
loadBalancerPrivateIP = ""

wikiConfigDestination = "/etc/nginx/conf.d/wiki-config.conf"
wikiConfigSource = "wiki-config_base.conf"
wikiConfigTemp = "wiki-config_base_temp.conf"
loadBalancerInstanceName = ""

# client info
clientCheckPort =
clientPrivateIP = ""
clientJarAddress = "/home/ubuntu/java_jar/traceReplay.jar"
maxClientMemory = "-Xmx4096M"
clientInstanceName = ""
clientInstanceID = ""

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
fixedWikiNodesCountOnD = 15
fixedWikiNodesCountBur = 15
sleepAfterNodeStartInSeconds=120
sleepAfterUpdatingNginxConfInSeconds=60