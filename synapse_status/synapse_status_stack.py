from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_ec2 as ec2,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct
from pathlib import Path

class SynapseStatusStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 statuspage_api_key: str,
                 statuspage_page_id: str,
                 statuspage_repo_component_id: str,
                 statuspage_website_component_id: str,
                 vpc_id: str,
                 exec_schedule_min: int,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, "SynapseVPC", vpc_id=vpc_id)

        lambda_role = iam.Role(self, "StatusUpdaterExecutionRole",
                               assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                               managed_policies=[
                                   iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
                               ]
                               )

        function = _lambda.Function(
            self, "StatusUpdaterFunction",
            runtime=_lambda.Runtime.NODEJS_22_X,
            handler="statuspage_updater.handler",
            code=_lambda.Code.from_asset(str(Path(__file__).parent.parent / "lambda")),
            environment={
                "REPO_STATUS_ENDPOINT": "https://repo-prod.prod.sagebase.org/repo/v1/status",
                "WEBSITE_URL_ENDPOINT": "https://www.synapse.org",
                "STATUS_PAGE_IO_API_KEY": statuspage_api_key,
                "STATUS_PAGE_IO_PAGE_ID": statuspage_page_id,
                "STATUS_PAGE_IO_REPO_COMPONENT_ID": statuspage_repo_component_id,
                "STATUS_PAGE_IO_WEBSITE_COMPONENT_ID": statuspage_website_component_id
            },
            role=lambda_role,
            timeout=Duration.seconds(30),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, availability_zones=['us-east-1a', 'us-east-1c'])
        )

        function.apply_removal_policy(RemovalPolicy.DESTROY)

        rule = events.Rule(
            self, "StatusScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(exec_schedule_min)),
        )
        rule.add_target(targets.LambdaFunction(function))