# UrbanFlow Infrastructure

This directory contains the Terraform configuration for deploying the UrbanFlow infrastructure on LocalStack.

## Prerequisites

The following tools are required to run the infrastructure and deployment scripts:

-   **Docker** & **Docker Compose**: To containerize and run LocalStack.
-   **Terraform**: To provision infrastructure as code.
-   **Python** (3.13): Required for Lambda function runtime.
-   **Node.js** & **npm**: Required for building the frontend.
-   **AWS CLI** (optional but recommended): For interacting with LocalStack manually.

## Setup & Deployment

1.  **Start LocalStack**
    Use Docker Compose to start the LocalStack service in the background:
    ```bash
    docker-compose up -d
    ```

2.  **Initialize Terraform**
    Navigate to the `infrastructure` directory:
    ```bash
    cd infrastructure
    terraform init
    ```

3.  **Deploy Resources**
    Apply the Terraform configuration to create Kinesis streams, DynamoDB tables, Lambda functions, and API Gateway.
    ```bash
    terraform apply
    ```
    Confirm with `yes` when prompted.

4.  **Deploy Frontend**
    Navigate to the `urban-flow-frontend` directory and run the deployment script:
    ```powershell
    cd ../urban-flow-frontend
    ./deploy-to-localstack.ps1
    ```

## Accessing the Application

**Important**: To access the application via the local domain, you must update your `hosts` file (e.g., `C:\Windows\System32\drivers\etc\hosts` on Windows) with the following lines:

```
127.0.0.1 localhost.localstack.cloud
127.0.0.1 urban-flow-frontend-local.s3-website.localhost.localstack.cloud
```

-   **Frontend URL**:
    ```
    http://urban-flow-frontend-local.s3-website.localhost.localstack.cloud:4566
    ```
-   **API Endpoint**:
    ```
    http://<api-id>.execute-api.localhost.localstack.cloud:4566
    ```

### Retrieve Outputs
If you need to see the URLs again later:
```bash
terraform output
```

## Testing

To verify that the Lambda functions and Kinesis streams are working correctly, you can run the provided test script. This script sends a record to the Kinesis stream and then queries the API Gateway to verify the data was processed.

1.  **Run the Test Script**
    Ensure you are in the `infrastructure` directory:
    ```bash
    ./test/test_lambdas.sh
    ```
    *Note: You might need to make the script executable first with `chmod +x test/test_lambdas.sh`.*

## Configuration

You can customize the deployment using `variables.tf` or by passing flags:
-   `lambda_batch_size`: Control the batch size for Kinesis event processing (default: 100).
