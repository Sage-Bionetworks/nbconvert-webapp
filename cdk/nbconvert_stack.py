from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_certificatemanager as acm,
    aws_apigateway as apigw,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct


class NBConvertLambdaCdkStack(Stack):


    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        DEV_CERT_ARN = "arn:aws:acm:us-east-1:449435941126:certificate/7d391bab-0663-4438-a418-2422b051adc7"
        PROD_CERT_ARN = "arn:aws:acm:us-east-1:325565585839:certificate/7c42c355-3d69-4537-a5e6-428212db646f"

        fct_stack = self.node.try_get_context('fct_stack') or 'dev'
        domain_prefix = f"api-{fct_stack}."

        if fct_stack == 'prod':
            cert_arn = PROD_CERT_ARN
        else:
            cert_arn = DEV_CERT_ARN

        self.lambda_fct = self.build_lambda_func(fct_stack=fct_stack)
        self.setup_api_gateway = self.setup_api_gateway(lambda_function=self.lambda_fct,
                                                        domain_name=f"{domain_prefix}synapse.org",
                                                        cert_arn=cert_arn,
                                                        base_path="nbconvert")

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
                directory="./nbconvert"
            ),
            timeout=Duration.seconds(120)
        )

    def setup_api_gateway(
        self,
        lambda_function: _lambda.DockerImageFunction,
        domain_name: str,
        cert_arn: str,
        base_path: str) -> apigw.RestApi:
        certificate = acm.Certificate.from_certificate_arn(
            self,
            "CustomDomainCert",
            cert_arn
        )

        domain_name_opts = apigw.DomainNameOptions(
            domain_name=domain_name,
            certificate=certificate,
        )

        resource_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.AnyPrincipal()],  # Public Access
            actions=["execute-api:Invoke"],
            resources=["*"]  # Allow all stages/methods
        )

        api = apigw.RestApi(
            self,
            "NBConvertApiGateway",
            rest_api_name="NBConvertAPI",
            domain_name=domain_name_opts,
            policy=iam.PolicyDocument(statements=[resource_policy]),
        )

        lambda_integration = apigw.LambdaIntegration(lambda_function)

        resource = api.root.add_resource(base_path)
        resource.add_method("GET", lambda_integration, authorization_type=apigw.AuthorizationType.NONE)

        lambda_function.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=self.format_arn(service="execute-api", resource=api.rest_api_id, resource_name=f"*/*/{base_path}")
        )

        CfnOutput(self, "ApiGatewayURL", value=api.url)

        return api
