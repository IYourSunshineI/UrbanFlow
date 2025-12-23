# UrbanFlow Infrastructure

This directory contains the Terraform configuration for deploying the UrbanFlow infrastructure on LocalStack.

## Prerequisites

- **LocalStack**: Ensure LocalStack is installed and running (`localstack start`).
- **Terraform**: Install Terraform to provision infrastructure.
- **Python**: Required for Lambda functions (runtime `python3.13`).
- **Node/npm**: Required for building the frontend (if running locally or via Amplify).

## Setup & Deployment

1.  **Start LocalStack**
    ```bash
    localstack start
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

## Troubleshooting

### API Gateway DNS Issues
If you encounter "Hmm we're having trouble finding that site" or DNS resolution errors for `*.localhost.localstack.cloud` domains, ensure your `hosts` file is correctly configured as shown above.

**Workaround**: Use the path-style URL for the API Gateway, which bypasses DNS subdomain resolution:
```
http://localhost:4566/_aws/execute-api/<api-id>/traffic
```
You can find this URL in the `local_api_url` output from Terraform.

### "UnrecognizedClientException"
If you see auth errors, ensure your `provider.tf` correctly points all services to `http://localhost:4566`.

## Configuration

You can customize the deployment using `variables.tf` or by passing flags:
-   `lambda_batch_size`: Control the batch size for Kinesis event processing (default: 100).
