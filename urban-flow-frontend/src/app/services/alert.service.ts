import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subject, Observable, timer, of } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { getAlertsApiUrl } from '../config/api.config';

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
  
  private lastAlertId: string | null = null;

  private alertSelectedSubject = new Subject<Alert>();
  public alertSelected$ = this.alertSelectedSubject.asObservable();

  constructor(private http: HttpClient) {
    this.startPolling();
  }

  selectAlert(alert: Alert) {
    this.alertSelectedSubject.next(alert);
  }

  getAlertsForSensor(sensorId: string): Observable<Alert[]> {
    return this.fetchAlerts(sensorId);
  }

  private startPolling() {
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
    const url = getAlertsApiUrl(sensorId);
    return this.http.get<Alert[]>(url);
  }

  private processAlerts(alerts: Alert[]) {
    if (!alerts || alerts.length === 0) return;

    const newestAlert = alerts[0];

    if (newestAlert.alert_id !== this.lastAlertId) {
      console.log('New Alert received:', newestAlert);
      this.lastAlertId = newestAlert.alert_id;
      this.alertsSubject.next(newestAlert);
    }
  }
}
