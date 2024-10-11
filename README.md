# AutoBurst

AutoBurst is published as a research paper in 15th ACM Symposium on Cloud Computing SoCC '24.

## Abstract

Burstable instances provide a low-cost option for consumers using the public cloud, but they come with significant resource limitations.
They can be viewed as "fractional instances" where one receives a fraction of the compute and memory capacity at a fraction of the cost of regular instances.
The fractional compute is achieved via rate limiting, where a unique characteristic of the rate limiting is that it allows for the CPU to burst to 100\% utilization for limited periods of time.
Prior research has shown how this ability to burst can be used to serve specific roles such as a cache backup and handling flash crowds.
Our work provides a general-purpose approach to meeting latency SLOs via this burst capability while optimizing for cost.
AutoBurst is able to achieve this by controlling both the number of burstable and regular instances along with how/when they are used.
Evaluations show that our system is able to reduce cost by up to $25\%$ over the state-of-the-art while maintaining latency SLOs.
