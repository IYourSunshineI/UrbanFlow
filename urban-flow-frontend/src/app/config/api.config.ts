/**
 * API Configuration for UrbanFlow Frontend
 * 
 * LocalStack API Gateway URL format:
 * http://localhost:4566/restapis/{api_id}/{stage}/_user_request_/{resource}
 */

export const environment = {
  production: false,

  // LocalStack API Gateway base URL
  // The API ID will need to be updated after terraform apply
  apiBaseUrl: 'http://localhost:4566/restapis',

  // Default stage name from Terraform
  apiStage: 'dev',

  // Traffic endpoint resource path
  trafficEndpoint: 'traffic',

  // Polling interval in milliseconds (how often to fetch new data)
  pollingIntervalMs: 5000,
};

/**
 * Build the full API URL for the traffic endpoint.
 * @param apiId - The API Gateway REST API ID (from terraform output)
 */
export function getTrafficApiUrl(apiId: string): string {
  return `${environment.apiBaseUrl}/${apiId}/${environment.apiStage}/_user_request_/${environment.trafficEndpoint}`;
}

/**
 * Build URL for a specific street
 */
export function getStreetTrafficUrl(apiId: string, streetId: string): string {
  return `${getTrafficApiUrl(apiId)}?street_id=${streetId}`;
}
