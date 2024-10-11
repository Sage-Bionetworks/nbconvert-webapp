from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda
)
from constructs import Construct
from aws_cdk.aws_ecr_assets import Platform

class NBConvertLambdaCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fct_stack = self.node.try_get_context('fct_stack') or 'dev'

        self.build_lambda_func(fct_stack=fct_stack)
        fct_url = self.prediction_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )

    def build_lambda_func(self, fct_stack):
        self.prediction_lambda = _lambda.DockerImageFunction(
            scope=self,
            id=f"{fct_stack}-nbconvert-lambda",
            # Function name on AWS
            function_name=f"{fct_stack}-nbconvert-lambda",
            # Use aws_cdk.aws_lambda.DockerImageCode.from_image_asset to build
            # a docker image on deployment
            code=_lambda.DockerImageCode.from_image_asset(
                # Directory relative to where you execute cdk deploy
                # contains a Dockerfile with build instructions
                directory="./nbconvert",
                platform=Platform.LINUX_AMD64
            ),
            timeout=Duration.seconds(120)
        )
