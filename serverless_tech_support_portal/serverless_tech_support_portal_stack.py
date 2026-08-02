import os

from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_cognito as cognito,
)
from constructs import Construct

class ServerlessTechSupportPortalStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = dynamodb.Table(
            self, "TicketsTable",
            partition_key=dynamodb.Attribute(
                name="ticket_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        ticket_queue = sqs.Queue(
            self, "TicketQueue",
            removal_policy=RemovalPolicy.DESTROY
        )

        ticket_topic = sns.Topic(
            self, "TicketTopic",
            display_name="Support Ticket Notifications"
        )

        user_pool = cognito.UserPool(
            self, "SupportPortalUserPool",
            user_pool_name="support-portal-users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            removal_policy=RemovalPolicy.DESTROY
        )

        # اضافه کردن دامنه کوگنیتو برای فعال‌سازی Hosted UI
        user_pool.add_domain(
            "CognitoDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="support-portal-users-785157631204"
            )
        )

        # تنظیم کلاینت برای پشتیبانی از Hosted UI و روش Authorization Code
        user_pool_client = user_pool.add_client(
            "WebAppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            oauth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True
                ),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                supported_identity_providers=[cognito.OAuthProvider.COGNITO],
                callback_urls=["http://localhost:3000/", "https://d123456789.cloudfront.net/"], # آدرس سایت خود را اینجا قرار دهید
                logout_urls=["http://localhost:3000/", "https://d123456789.cloudfront.net/"]
            )
        )

        my_lambda = _lambda.Function(
            self, "SupportLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_inline("""
import json
import os
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)
sqs = boto3.client('sqs')
sns = boto3.client('sns')

queue_url = os.environ.get('QUEUE_URL')
topic_arn = os.environ.get('TOPIC_ARN')

def handler(event, context):
    http_method = event.get('httpMethod', 'GET')
    
    if http_method == 'POST':
        try:
            body = json.loads(event.get('body', '{}'))
            ticket_id = str(uuid.uuid4())
            ticket_data = {
                'ticket_id': ticket_id,
                'subject': body.get('subject', 'No Subject'),
                'description': body.get('description', ''),
                'status': 'OPEN'
            }
            
            table.put_item(Item=ticket_data)
            
            if queue_url:
                sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(ticket_data)
                )
            
            if topic_arn:
                sns.publish(
                    TopicArn=topic_arn,
                    Subject='New Support Ticket Created',
                    Message=f"A new support ticket has been created with ID: {ticket_id}"
                )
            
            return {
                'statusCode': 201,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({'message': 'Ticket created successfully', 'ticket': ticket_data})
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({'error': str(e)})
            }
            
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({'message': 'Welcome to Tech Support Portal API. Use POST to create a ticket.'})
    }
"""),
            handler="index.handler"
        )

        table.grant_read_write_data(my_lambda)
        ticket_queue.grant_send_messages(my_lambda)
        ticket_topic.grant_publish(my_lambda)

        my_lambda.add_environment("TABLE_NAME", table.table_name)
        my_lambda.add_environment("QUEUE_URL", ticket_queue.queue_url)
        my_lambda.add_environment("TOPIC_ARN", ticket_topic.topic_arn)

        auth = apigw.CognitoUserPoolsAuthorizer(
            self, "PortalAuthorizer",
            cognito_user_pools=[user_pool]
        )

        api = apigw.LambdaRestApi(
            self, "SupportApi",
            handler=my_lambda,
            proxy=True,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            ),
            default_method_options=apigw.MethodOptions(
                authorizer=auth,
                authorization_type=apigw.AuthorizationType.COGNITO
            )
        )

        site_bucket = s3.Bucket(
            self, "TicketSiteBucket",
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        current_dir = os.path.dirname(__file__)
        frontend_path = os.path.join(current_dir, "..", "frontend")
        
        s3_deploy.BucketDeployment(
            self, "DeployWebsite",
            sources=[s3_deploy.Source.asset(frontend_path)],
            destination_bucket=site_bucket
        )

        CfnOutput(
            self, "SiteURL",
            value=site_bucket.bucket_website_url,
            description="The public URL of the static tech support portal"
        )
        
        CfnOutput(
            self, "UserPoolIdOutput",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        CfnOutput(
            self, "ClientIdOutput",
            value=user_pool_client.user_pool_client_id,
            description="Cognito Client ID"
        )