FROM public.ecr.aws/lambda/python:3.11

# Install zmq dependencies
RUN yum install -y gcc libzmq3-dev

# Install pyzmq
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip3 install -r ./requirements.txt

# Copy lambda function code
COPY service.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your function handler
CMD ["service.handler"]
