class Node:
    def __init__(self, info, weight, baseCreditBalance=0, creditBalance=0):
        self.info = info
        self.weight = weight
        self.baseCreditBalance = baseCreditBalance
        self.creditBalance = creditBalance

    def __str__(self):
        return self.info["InstanceType"] + " " + self.info["PrivateIpAddress"] + " "+ self.info["InstanceId"] + " " + str(self.weight)