# nbconvert-webapp
Converts ipynb file into html.
This is a light wrapper around [nbconvert](https://github.com/jupyter/nbconvert), packaged to deploy as an [AWS Lambda](https://aws.amazon.com/lambda) function.

Note, I used [python-lambda](https://github.com/nficano/python-lambda) as a starting point.

## How to create the deployment package
Note that a prebuilt package is included in the dist directory.  To rebuild...
As described in the [AWS Lambda "Creating a Deployment Package (Python)" doc](http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html), use the Virtualenv tool.
Install all dependencies within this environment
```
pip install requests
pip install nbconvert
```
Now zip up your site-packages directory.  I named the archive `app.zip`

Then add the handler file, service.py, to the app.zip
```
zip -g app.zip service.py
```

## [How to deploy the AWS Lambda Function deployment package](http://docs.aws.amazon.com/lambda/latest/dg/vpc-rds-upload-deployment-pkg.html)
To create the function:
```
## <bucket_name> is the name of the bucket where the package resides
## <lambda_role_arn> is the arn of the role to be assumed by the lambda function
aws lambda create-function --region <region> --function-name nbconvert --code S3Bucket=<bucket_name>,S3Key=app.zip --role <lambda_role_arn> --handler service.handler --runtime python3.6 --timeout 10 --memory-size 1024
```
To update the function:
```
aws lambda update-function-code --function-name nbconvert --s3-bucket <bucket_name> --s3-key=app.zip --publish
```

## How to test locally
Install the python-lambda helper project:
```
pip install python-lambda
```
Now call the lambda handler (service.py using event.json as input) by executing the command:
```
lambda invoke -v
```
