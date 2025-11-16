from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_certificatemanager as acm,
    aws_apigatewayv2 as apigw2,
    aws_apigatewayv2_integrations as apigw2_integrations,
    aws_apigatewayv2_authorizers as apigw2_authorizers,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct

SYNAPSE_OAUTH_CLIENT_ID = "0"

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
        self.setup_api_gateway = self.setup_api_gateway(fct_stack=fct_stack,
                                                        lambda_function=self.lambda_fct,
                                                        domain_name=f"{domain_prefix}synapse.org",
                                                        cert_arn=cert_arn,
                                                        base_path="nbconvert")

    def build_lambda_func(self, fct_stack:str ) -> _lambda.DockerImageFunction:
        return _lambda.DockerImageFunction(
            scope=self,
            id=f"{fct_stack}-nbconvert-lambda",
            function_name=f"{fct_stack}-nbconvert-lambda",
            code=_lambda.DockerImageCode.from_image_asset(
                directory="./nbconvert"
            ),
            timeout=Duration.seconds(120)
        )

    def setup_api_gateway(
        self,
        fct_stack: str,
        lambda_function: _lambda.DockerImageFunction,
        domain_name: str,
        cert_arn: str,
        base_path: str) -> apigw2.HttpApi:

        certificate = acm.Certificate.from_certificate_arn(
            self,
            id="CustomDomainCert",
            certificate_arn=cert_arn
        )

        allowed_origins = ["*"]
        if fct_stack == 'prod':
            allowed_origins = ["https://www.synapse.org", "https://synapse.org"]

        api = apigw2.HttpApi(
            self,
            id="NBConvertApiGateway",
            api_name="NBConvertAPI",
            cors_preflight={
                "allow_origins": allowed_origins,
                "allow_methods": [apigw2.CorsHttpMethod.GET],
                "allow_headers": ["*"]
            }
        )

        jwt_auth = apigw2_authorizers.HttpJwtAuthorizer(
            id="NBConvertJwtAuthorizer",
            jwt_issuer=f"https://repo-prod.{fct_stack}.sagebase.org/auth/v1",
            jwt_audience=[SYNAPSE_OAUTH_CLIENT_ID],
        )

        lambda_integration = apigw2_integrations.HttpLambdaIntegration(
            id="LambdaIntegration",
            handler=lambda_function
        )

        api.add_routes(
            path=f"/{base_path}",
            methods=[apigw2.HttpMethod.GET],
            integration=lambda_integration,
            authorizer=jwt_auth
        )

        domain_name = apigw2.DomainName(
            self,
            id="CustomDomain",
            domain_name=domain_name,
            certificate=certificate,
        )

        apigw2.ApiMapping(
            self,
            id="ApiMapping",
            api=api,
            domain_name=domain_name,
            stage=api.default_stage
        )

        CfnOutput(self, "ApiGatewayURL", value=api.url)

        return api
