/**
 * API Configuration for UrbanFlow Frontend
 *
 * LocalStack API Gateway URL format:
 * http://localhost:4566/restapis/{api_id}/{stage}/_user_request_/{resource}
 *
 * After terraform apply, update apiId below with: terraform output -raw api_id
 */

export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:4566/restapis',
  apiId: 'iianki73yo', // <- UPDATE THIS after terraform apply
  apiStage: 'dev',
  trafficEndpoint: 'traffic',
  alertsEndpoint: 'alerts',
  pollingIntervalMs: 5000,
  websocketUrl: 'wss://placeholder-url',
};

export function getTrafficApiUrl(): string {
  return `${environment.apiBaseUrl}/${environment.apiId}/${environment.apiStage}/_user_request_/${environment.trafficEndpoint}`;
}

export function getStreetTrafficUrl(streetId: string): string {
  return `${getTrafficApiUrl()}?street_id=${streetId}`;
}

export function getAlertsApiUrl(sensorId?: string): string {
  let url = `${environment.apiBaseUrl}/${environment.apiId}/${environment.apiStage}/_user_request_/${environment.alertsEndpoint}`;
  if (sensorId) {
    url += `?street_id=${sensorId}`;
  }
  return url;
}
