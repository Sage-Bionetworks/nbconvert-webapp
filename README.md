# nbconvert-webapp
Creates an API backed by a lambda to convert a notebook
to HTML. The Synapse portal calls the API to display a
a preview of a notebook file.

This is a light wrapper around [nbconvert](https://github.com/jupyter/nbconvert), packaged to deploy as an [AWS Lambda](https://aws.amazon.com/lambda) function.
Note, I used [python-lambda](https://github.com/nficano/python-lambda) as a starting point.

The deployment uses the AWS CDK to create the function (packaged as
a docker container) and associated API Gateway.
