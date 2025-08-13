# synapse-status-lambda
This project contains the lambda used to update Synapse's status on StatusPage.io.

The lambda runs on a schedule (typically 5 mins)
- uses the Synapse API to get the current status for the Repository service and the Synapse portal
- uses the Statuspage.io API to update their corresponding statuses on https://synapse.statuspage.io/

Deployment is done with Github workflow with the following parameters (in deploy.yml):
- VPC_ID: <vpc_where_lambda_is_deployed>
- AVAILABLE_ZONES: <comma_delimited_string_of_zones> , ("us-east-1a, us-east-1b")
- STATUSPAGE_API_KEY: ${{ secrets.STATUSPAGE_API_KEY }} , key is stored as secret in the prod enviroment
- STATUSPAGE_PAGE_ID: <pageId_in_statuspage>
- STATUSPAGE_REPO_COMPONENT_ID: <repo_componentId_in_statuspage>
- STATUSPAGE_WEBSITE_COMPONENT_ID: <portal_componentId_in_statuspage>
- EXEC_SCHEDULE_MIN: <[schedule_expression](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-scheduled-rule-pattern.html)>

For more information about StatusPage.io API, see https://developer.statuspage.io/