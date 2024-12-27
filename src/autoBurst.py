import throughputTableUtilities as tTableUtilities

class AutoBurstPolicies():
    def __init__(self, H, L, onDnodes, burNodes, meanSLO, P, D, throughputfilename, potentialIncreaseFactor, desiredLoad, P_m, D_m, desiredCredit):
        self.H = H
        self.L = L
        self.burNodes = burNodes
        self.onDnodes = onDnodes
        self.meanSLO = meanSLO
        self.P = P
        self.D = D
        self.P_m = P_m
        self.D_m = D_m
        self.error = []
        self.errorSum = 0
        self.lweight = 0
        self.potentialIncreaseFactor = potentialIncreaseFactor
        self.desiredLoad = desiredLoad
        table, onDlim, burlim = tTableUtilities.readTable(throughputfilename)
        self.throughputTable = table
        tTableUtilities.fillUpThroughputTable(self.throughputTable, onDlim, burlim)
        self.creditTotal = []
        self.increaseOnDflag = 0
        self.difflist = []
        self.desiredCredit = desiredCredit

        self.initialStartTime = datetime.datetime.now()


    def init_weight(self, onD, bur, weight):
        self.lweight = max(min(math.log10(weight), math.log10(self.H)), math.log10(self.L))

        for instance in onD:
            instance.weight = self.H

        for instance in bur:
            instance.weight = int(max(min(weight, self.H), self.L))


    """
    Calculates the total credit balance for burstable instances and reserved burstable instances.

    Parameters:
    - bur (list): List of currently running burstable instances.
    - stop_pending (list): List of burstable instances pending termination.

    Returns:
    - tuple: 
        - totalresburCredit (int): Total credit balance of reserved burstable instances (currently unused and default to 0).
        - totalburCredit (int): Total credit balance of running and pending burstable instances.

    """

    def getCreditTotal(self, bur, stop_pending):
        totalburCredit = 0
        for instance in bur:
            cred = InstanceUtility.getCredit(instance.info["InstanceId"], "Average")[0]
            instance.creditBalance = cred
            totalburCredit += cred
            print("Instance credit = ", instance.creditBalance)

        for instance in stop_pending:
            cred = InstanceUtility.getCredit(instance.info["InstanceId"], "Average")[0]
            instance.creditBalance = cred
            totalburCredit += cred
            print("Instance credit = ", instance.creditBalance)

        totalresburCredit = 0

        print("Total credit of burstables = ", totalburCredit, " and reserved burstable = ", totalresburCredit)
        return totalresburCredit, totalburCredit


    """
    Gets the expectedCredit. Currently returns a fixed value set by the user. However, can be set dynamically based on desiredThroughput

    Parameters:
        desiredThroughput (int): The desired throughput of the system
        
    Returns:
        - desiredCredit (int): 
    """
    def getExpectedCredit(desiredThroughput):
        return self.desiredCredit
    """
    Estimates the adjustments needed for on-demand and burstable resources to optimize throughput 
    while balancing credit utilization and resource constraints.

    Parameters:
        r (int): The number of reserved instances currently allocated.
        rb (int): The number of reserved burstable instances currently allocated.
        arrRate (float): The incoming arrival rate of requests.
        bur (list): A list of active burstable instance objects. Each instance is expected to have a `creditBalance` and `weight` attribute.
        stop_pending (list): A list of burstable instances marked for termination. Each instance is expected to have a `creditBalance` and `weight` attribute.
        onD (int): The number of on-demand instances currently allocated. Each instance is expected to have a `creditBalance` and `weight` attribute.

    Returns:
        tuple:
            - numberofonD (int): The number of additional or reduced on-demand instances.
            - numberofbur (int): The number of additional or reduced burstable instances.

    """


    def resource_estimator(self, arrRate, bur, stop_pending, onD, unused_onD):
        

        desiredThroughput = arrRate * self.potentialIncreaseFactor / self.desiredLoad
        resBurcredit, burcredit = self.getCreditTotal(bur, stop_pending)
        creditTotal = resBurcredit + burcredit
        
        self.creditTotal.append(creditTotal)

    
        currentTime = datetime.datetime.now()
        timeSpent = (currentTime - self.initialStartTime).total_seconds() / 60

        getExpectedCredit(desiredThroughput)
     
        diff = expectedCredit - creditTotal
        self.difflist.append(diff)

        if len(self.difflist) > 3:
            self.difflist.pop(0)

        if len(self.difflist) < 2:
            out = self.P_m * self.difflist[-1]
        else:
            out = (self.P_m * self.difflist[-1]) + (self.D_m * (self.difflist[-1] - self.difflist[-2]))

        bound = 1
        if out > bound:
            out = bound
        elif out < -bound:
            out = -bound

        self.increaseOnDflag += out

        changeVal = 0
        while self.increaseOnDflag >= 1:
            # onD += 1
            changeVal += 1
            self.increaseOnDflag -= 1
        while self.increaseOnDflag <= -1:
            # onD -= 1
            changeVal -= 1
            self.increaseOnDflag += 1

        if changeVal > unused_onD:
            changeVal = unused_onD

        onD += changeVal
        if onD < 0:
            onD = 0

        
        b = tTableUtilities.findNumberOfBurstable(self.throughputTable, onD, desiredThroughput, 0)
        if b == -1:
            b = len(bur)
        numberofonD = onD
        numberofbur = b
        return numberofonD, numberofbur


    """
    Adjusts the weights of instances based on latency deviation from a Service Level Objective (SLO).

    Parameters:
        onD (list): Currently unused parameter (can be removed if unnecessary).
        bur (list): A list of "burstable" instances whose weights are to be optimized. Each instance is expected 
                    to have a `creditBalance` and `weight` attribute.
        latency (list): A list containing the latency measurements (in nanoseconds). Only the first value in this 
                        list is used for optimization.
        bur_stop_pending (list): A list of burstable instances that are pending termination or stopping. Their 
                                 weights are adjusted with an additional bias.
    """
    def latency_optimizer(self, bur, latency, bur_stop_pending):
        if len(latency) == 0:
            return
        latencyVal = int(latency[0]) / 1000000000

        currentError = latencyVal - self.meanSLO
        self.error.append(currentError)
        if len(self.error) > 3:
            self.error.pop(0)

        if len(self.error) < 2:
            out = self.P * self.error[-1]
        else:
            out = (self.P * self.error[-1]) + (self.D * (self.error[-1] - self.error[-2]))

        self.lweight = max(min(self.lweight + out, math.log10(self.H)), math.log10(self.L))
        

        minCredit = bur[0].creditBalance
        for instance in bur:
            if instance.creditBalance < minCredit:
                minCredit = instance.creditBalance

        for instance in bur:
            weight = pow(10, self.lweight)
            if instance.creditBalance == minCredit:
                weight = weight - 1
            instance.weight = int(max(min(weight, self.H), self.L))
            
        for instance in bur_stop_pending:
            weight = pow(10, self.lweight + 0.1)
            instance.weight = int(max(min(weight, self.H), self.L))
            