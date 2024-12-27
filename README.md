# AutoBurst

AutoBurst is published as a research paper in 15th ACM Symposium on Cloud Computing SoCC '24.

## Citing the paper
```bibtex
@inproceedings{10.1145/3698038.3698530,
author = {Hasan, Rubaba and Zhu, Timothy and Urgaonkar, Bhuvan},
title = {AutoBurst: Autoscaling Burstable Instances for Cost-effective Latency SLOs},
year = {2024},
isbn = {9798400712869},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3698038.3698530},
doi = {10.1145/3698038.3698530},
booktitle = {Proceedings of the 2024 ACM Symposium on Cloud Computing},
pages = {243–258},
numpages = {16},
keywords = {Autoscaling, Burstable Instances, Cloud Computing, Resource Provisioning},
location = {Redmond, WA, USA},
series = {SoCC '24}
}
```

## Abstract

Burstable instances provide a low-cost option for consumers using the public cloud, but they come with significant resource limitations.
They can be viewed as "fractional instances" where one receives a fraction of the compute and memory capacity at a fraction of the cost of regular instances.
The fractional compute is achieved via rate limiting, where a unique characteristic of the rate limiting is that it allows for the CPU to burst to 100\% utilization for limited periods of time.
Prior research has shown how this ability to burst can be used to serve specific roles such as a cache backup and handling flash crowds.
Our work provides a general-purpose approach to meeting latency SLOs via this burst capability while optimizing for cost.
AutoBurst is able to achieve this by controlling both the number of burstable and regular instances along with how/when they are used.
Evaluations show that our system is able to reduce cost by up to $25\%$ over the state-of-the-art while maintaining latency SLOs.

## Requirements

This code needs Python 3.8.10 and Java 17+

## How to use

To run the autoBurst controller:
```bash
python3 autoBurstController.py --configFile <configFilePath>
```

AutoBurst is based on AWS and assumes all components are in AWS.

The following nodes have to be in place before running the AutoBurst Controller:

### LoadBalancer
nginx loadbalancer is used in a separate node. Install nginx from the source code in the folder nginx (Version: nginx/1.18.0).

Or, get the source code for nginx and in the file /src/http/modules/ngx_stream_upstream_least_conn_module.c in nginx, change the following line: 
```
peer->conns / peer->weight < best->conns / best->weight 
```
to 
```
(peer->conns + 1) * best->weight < (best->conns + 1) * peer->weight
```
Update the following variables in Variables.py -
LB_INSTANCE_ID 
loadBalancerPrivateIP 

### Client
Put the java_jar/traceReplay.jar file in a client instance. Results are stored in "/home/ubuntu/results/experimentname" in the client instances.  Update the following variables in Variables.py- 
clientCheckPort
clientPrivateIP
clientJarAddress
clientInstanceName
clientInstanceID

### Wikimedia, cache and database

Link for installing wikimedia: https://www.digitalocean.com/community/tutorials/how-to-install-mediawiki-on-ubuntu-14-04

Also install memcacheD in the wikimedia instance and connect the wikimedia instance to a database in a separate instance

Update the following variables in Variables.py based on the wikimedia instance image and the database- 

WIKI_OND_IMAGE_ID = ""

WIKI_BUR_IMAGE_ID =  ""

DB_INSTANCE_PREFIX = ""
DB_IMAGE_NAME = ""
dbPort = 
DB_INSTANCE_LIST = [{"instanceName": "", "InstanceId": ""}]
DBcount =

### Config files:

Update the config/config.json file and the Variables.py file with the configurations.

#### config.json:
```json
"experimentName": Name of the experiment
"H": Maximum (int) value of weight of an instance
"L": Minimum (int) value of weight of an instance
"onDnodes": Initial number of on-demand instances
"burNodes": Initial number of burstable instances
"meanSLO": The user-specified mean latency SLO
"P": P- term for latency optimizer
"D": D- term for latency optimizer
"throughputfilename": Throughput file
"potentialIncreaseFactor": A factor by which load can be increased to allow variability
"desiredLoad": User expectation for the load to be compared to max load
"P_m": P- term for resource estimator
"D_m": D- term for resource estimator
"durationRE": Duration of resource estimator, in seconds
"durationLE": Duration of latency optimizer, in seconds
"desiredCredit": Desired credit value
```

#### Varibles.py
```
key = key for AWS access

keyName = name of AWS key
securityGroup = AWS security group where the application is deployed
placement = The AWS availability zone where the application is deployed

##### DB
DB_INSTANCE_PREFIX = Prefix for database name
dbPort = Port that the database uses
DB_INSTANCE_LIST = list of instance name and instance ID for each database instance
DBcount = Number of database instances used


##### WIKI
WIKI_INSTANCE_PREFIX = Prefix for wikimedia instance names
WIKI_securityGroup = AWS security group where the application is deployed
WIKI_placement = The AWS availability zone where the application is deployed
WIKI_monitoring = "Enabled=true"
wikiPort = Port that the wiki instances use
startWikiIndex = Index value to track different wiki instances
localSettingsDestination = Destination for the localsettings file for mediawiki
localSettingsSource = "LocalSettings_base.php"
localSettingsTemp = "LocalSettings_temp.php"
localSettingsDefaultServerString = '$wgServer="http://0.0.0.0";'
localSettingsDefaultDbString = '$wgDBserver = "";'
localSettingsDefaultMemcachedString = '$wgMemCachedServers = [""];'


WIKI_OND_IMAGE_ID = Image ID for wikimedia installation

WIKI_BUR_IMAGE_ID =  Image ID for wikimedia installation

burstable_vcpu_baseline = {"t2.large": (2, 0.3), "t4g.large": (2, 0.3), "t3.large": (2, 0.3), "t3.small": (2, 0.2)}


##### load balancer info
LB_INSTANCE_PREFIX = Prefix for load balancer
LB_INSTANCE_ID = Instance ID for the loadbalancer
loadBalancerPrivateIP = Private IP address for the load balancer

wikiConfigDestination = Config file destination for the load balancer
wikiConfigSource = Config file source for the load balancer
wikiConfigTemp = Temporary file for the load balancer
loadBalancerInstanceName = Load balancer instance name

##### client info
clientCheckPort = Client port
clientPrivateIP = Private IP for client instance
clientJarAddress = Client jar file address
maxClientMemory = Max value for memory 
clientInstanceName = Name for client instance
clientInstanceID = Client instance ID


##### experiment info
resultDirPathClient = Result directory in client
clientBaseConfig = Config file base
tempClientConfig = Config file temporary
finalClientConfig = Path for config file in client
resultStorageDirectory =  Result directory

fixedWikiNodesCountOnD = Maximum number of on-demand nodes for the experiment
fixedWikiNodesCountBur = Maximum number of burstable nodes for the experiment
sleepAfterNodeStartInSeconds=120
sleepAfterUpdatingNginxConfInSeconds=60
```