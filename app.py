#!/usr/bin/env python3
import os
import aws_cdk as cdk

from synapse_status.synapse_status_stack import SynapseStatusStack


def get_required_env(key: str) -> str:
  value = os.environ.get(key)
  if value is None or value == "":
    raise ValueError(f"Missing environment variable: {key}")
  return value

def get_required_schedule_expression_env(time_expr: str) -> str:
    time_expr = time_expr.strip().lower()
    
    VALID_UNITS = [ "seconds", "minutes", "hours" ]

    # Split into value and unit
    parts = time_expr.split()
    
    if len(parts) != 2:
        raise ValueError(f"Invalid time expression format: {time_expr}. Expected format: '<number> <unit>'")
    
    value, unit = parts
    
    # Validate the unit
    if unit not in VALID_UNITS:
        raise ValueError(f"Invalid time unit: {unit}. Must be one of: {', '.join(VALID_UNITS)}")
    
    # Validate the value is a positive integer
    try:
        number = int(value)
        if number <= 0:
            raise ValueError
    except ValueError:
        raise ValueError(f"Invalid time value: {value}. Must be a positive integer")
    
    return f"rate({value} {unit})"


app = cdk.App()
SynapseStatusStack(app, "SynapseStatusStack",
                   env = cdk.Environment(account=get_required_env("ACCOUNT_ID"), region="us-east-1"),
                   statuspage_api_key = get_required_env("STATUSPAGE_API_KEY"),
                   statuspage_page_id = get_required_env("STATUSPAGE_PAGE_ID"),
                   statuspage_repo_component_id = get_required_env("STATUSPAGE_REPO_COMPONENT_ID"),
                   statuspage_website_component_id = get_required_env("STATUSPAGE_WEBSITE_COMPONENT_ID"),
                   vpc_id = get_required_env("VPC_ID"),
                   available_zones=[zone.strip() for zone in get_required_env("AVAILABLE_ZONES").split(",")],
                   exec_schedule_expression= get_required_schedule_expression_env("EXEC_SCHEDULE_EXPRESSION")
                   )

app.synth()