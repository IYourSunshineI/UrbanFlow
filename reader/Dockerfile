FROM public.ecr.aws/lambda/python:3.11

COPY reader.py ${LAMBDA_TASK_ROOT}

CMD ["reader.lambda_handler"]