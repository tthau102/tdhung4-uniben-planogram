import aws_cdk as core
import aws_cdk.assertions as assertions

from planogram_project_cdk.planogram_project_cdk_stack import PlanogramProjectCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in planogram_project_cdk/planogram_project_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PlanogramProjectCdkStack(app, "planogram-project-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
