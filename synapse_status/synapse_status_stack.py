
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    RemovalPolicy,
    Fn
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
                 available_zones: list[str],
                 exec_schedule_expression: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, "SynapseVPC", vpc_id=vpc_id)

        lambda_role = iam.Role(self, "StatusUpdaterExecutionRole",
                               assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                               managed_policies=[
                                   iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                                   iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
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
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, availability_zones=available_zones)
        )

        function.apply_removal_policy(RemovalPolicy.DESTROY)

        rule = events.Rule(
            self, "StatusScheduleRule",
            schedule=events.Schedule.expression(exec_schedule_expression),
        )
        rule.add_target(targets.LambdaFunction(function))

        # The handler rethrows after attempting both updates, so any failed update shows up as an error
        errors_alarm = cloudwatch.Alarm(
            self, "StatusUpdaterErrorsAlarm",
            alarm_description="Synapse StatusPage updater Lambda failed; StatusPage components may be stale.",
            metric=function.metric_errors(period=Duration.minutes(5), statistic="Sum"),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        alarm_topic = sns.Topic.from_topic_arn(
            self, "AlarmTopic",
            Fn.import_value("us-east-1-synapse-prod-global-resources-NotificationTopic"))
        errors_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))
        errors_alarm.add_ok_action(cw_actions.SnsAction(alarm_topic))
