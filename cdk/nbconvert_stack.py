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

        self.lambda_fct = self.build_lambda_func(fct_stack=fct_stack)

        # function URL with public access
        # Note: might want to specify _lambda.FunctionUrlAuthType.AWS_IAM
        # or use VPC endpoint to keep private
        self.fct_url = self.lambda_fct.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )

    def build_lambda_func(self, fct_stack:str ) -> _lambda.DockerImageFunction:
        return _lambda.DockerImageFunction(
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
                architecture=_lambda.Architecture.X86_64
            ),
            timeout=Duration.seconds(120)
        )
