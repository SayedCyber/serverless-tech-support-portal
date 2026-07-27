import aws_cdk as core
import aws_cdk.assertions as assertions

from serverless_tech_support_portal.serverless_tech_support_portal_stack import ServerlessTechSupportPortalStack

# example tests. To run these tests, uncomment this file along with the example
# resource in serverless_tech_support_portal/serverless_tech_support_portal_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ServerlessTechSupportPortalStack(app, "serverless-tech-support-portal")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
