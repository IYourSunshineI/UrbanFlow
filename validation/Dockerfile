FROM public.ecr.aws/lambda/python:3.11

COPY validator.py ${LAMBDA_TASK_ROOT}

CMD ["validator.lambda_handler"]