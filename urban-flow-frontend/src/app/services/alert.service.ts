import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subject, Observable, timer, of } from 'rxjs';
import { switchMap, map, catchError, shareReplay, distinctUntilChanged } from 'rxjs/operators';
import { environment, getTrafficApiUrl } from '../config/api.config';

export interface Alert {
  alert_id: string;
  sensor_id: string;
  street_name: string;
  timestamp: string;
  type: string;
  location: { lat: number; lng: number };
  details: any;
}

@Injectable({
  providedIn: 'root'
})
export class AlertService {
  private alertsSubject = new Subject<Alert>();
  public alerts$ = this.alertsSubject.asObservable();
  
  // Cache the last seen alert ID to avoid spamming the same alert
  private lastAlertId: string | null = null;

  // Output for interaction
  private alertSelectedSubject = new Subject<Alert>();
  public alertSelected$ = this.alertSelectedSubject.asObservable();

  constructor(private http: HttpClient) {
    this.startPolling();
  }

  // Called when "Anzeigen" is clicked
  selectAlert(alert: Alert) {
    this.alertSelectedSubject.next(alert);
  }

  // Fetch history for sidebar
  getAlertsForSensor(sensorId: string): Observable<Alert[]> {
    return this.fetchAlerts(sensorId);
  }

  private startPolling() {
    // Poll every 5 seconds
    timer(0, 5000).pipe(
      switchMap(() => this.fetchAlerts()),
      catchError(err => {
        console.error('Error fetching alerts:', err);
        return of([]);
      })
    ).subscribe(alerts => {
      this.processAlerts(alerts);
    });
  }

  private fetchAlerts(sensorId?: string): Observable<Alert[]> {
    // The alerts endpoint is at the same base URL but resource is 'alerts'
    // apiBaseUrl: http://localhost:4566/restapis
    // apiId: 7fkhcwqihv
    // stage: dev
    // url: .../traffic -> replace with /alerts
    
    // Quick hack to construct URL, better to have a config helper
    // Calling getTrafficApiUrl getting .../traffic and replacing
    const trafficUrl = getTrafficApiUrl(environment.apiBaseUrl.split('/')[4] || '7fkhcwqihv'); 
    // Wait, apiId needs to be known. 
    // In traffic.service, apiId is private. 
    // Ideally apiId should be in a shared config or service.
    // For now, let's look at how traffic.service gets it, it has it hardcoded now.
    
    // We will hardcode it here too for now as per the task context, 
    // or better, update api.config to have it.
    const apiId = '7fkhcwqihv';
    let url = `${environment.apiBaseUrl}/${apiId}/${environment.apiStage}/_user_request_/alerts`;
    
    if (sensorId) {
      url += `?street_id=${sensorId}`;
    }

    return this.http.get<Alert[]>(url);
  }

  private processAlerts(alerts: Alert[]) {
    if (!alerts || alerts.length === 0) return;

    // We assume the backend sorts by timestamp desc (newest first)
    const newestAlert = alerts[0];

    // If it's a new alert we haven't seen recently
    if (newestAlert.alert_id !== this.lastAlertId) {
      console.log('New Alert received:', newestAlert);
      this.lastAlertId = newestAlert.alert_id;
      this.alertsSubject.next(newestAlert);
    }
  }
}
