#!/bin/bash


# Fetch instance IDs and terminate
instance_ids=$(aws ec2 describe-instances \
  --region us-west-2 \
  --filters "Name=tag:Name,Values=*wiki*" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text --no-cli-pager)

if [ -n "$instance_ids" ]; then
  aws ec2 terminate-instances \
    --region us-west-2 \
    --instance-ids $instance_ids --no-cli-pager
  echo "Termination initiated for instances: $instance_ids"
else
  echo "No instances found with 'wiki' in their name."
fi