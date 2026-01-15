import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, interval, Subscription, catchError, of, switchMap, tap } from 'rxjs';
import { environment, getTrafficApiUrl } from '../config/api.config';

export interface Sensor {
  id: string;
  name: string;
  location: { lat: number; lng: number };
  description: string;
}

export interface TrafficData {
  sensorId: string;
  timestamp: Date;
  avgSpeed: number;
  vehicleCount: number;
  congestionIndex: number;
  status: 'free' | 'dense' | 'near_capacity' | 'congested';
  history: number[];
  vehicleHistory?: number[];
  name: string;
  location: { lat: number; lng: number };
  description?: string;
  speedLimit: number;
}

interface ApiTrafficData {
  street_id: string;
  street_name: string;
  average_speed_kph: number;
  speed_limit_kph: number;
  vehicle_count: number;
  congestion_index: number;
  timestamp_utc: string;
  latitude: number;
  longitude: number;
}

@Injectable({
  providedIn: 'root'
})
export class TrafficService implements OnDestroy {
  private sensors: Sensor[] = [
    { id: 'S1', name: 'Main St', location: { lat: 40.7128, lng: -74.0060 }, description: 'Downtown' },
    { id: 'S2', name: 'Broadway', location: { lat: 40.7580, lng: -73.9855 }, description: 'Midtown' },
    { id: 'S3', name: 'Wall St', location: { lat: 40.7060, lng: -74.0088 }, description: 'Financial District' }
  ];

  private trafficState = new BehaviorSubject<Map<string, TrafficData>>(new Map());
  private historyBuffer = new Map<string, { speeds: number[], counts: number[] }>();
  private pollingSub: Subscription | null = null;
  private useMockData = false;
  private mockInterval: any;

  public trafficData$ = this.trafficState.asObservable();

  constructor(private http: HttpClient) {
    this.startPolling();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  setUseMockData(useMock: boolean): void {
    this.useMockData = useMock;
  }

  private startPolling(): void {
    this.fetchTrafficData();

    this.pollingSub = interval(environment.pollingIntervalMs).pipe(
      switchMap(() => this.useMockData ? of(null) : this.fetchFromApi()),
      catchError(err => {
        console.error('Error fetching traffic data:', err);
        return of(null);
      })
    ).subscribe();

    if (this.useMockData) {
      this.startMockSimulation();
    }
  }

  private stopPolling(): void {
    if (this.pollingSub) {
      this.pollingSub.unsubscribe();
      this.pollingSub = null;
    }
  }

  private fetchTrafficData(): void {
    if (this.useMockData) {
      this.generateMockData();
    } else {
      this.fetchFromApi().subscribe();
    }
  }

  private fetchFromApi() {
    const url = getTrafficApiUrl();

    return this.http.get<ApiTrafficData[]>(url).pipe(
      tap(data => {
        if (Array.isArray(data)) {
          this.processApiData(data);
        }
      }),
      catchError(err => {
        console.error('API fetch failed, falling back to mock data:', err);
        this.generateMockData();
        return of(null);
      })
    );
  }

  private processApiData(apiData: ApiTrafficData[]): void {
    const newData = new Map<string, TrafficData>();

    apiData.forEach(item => {
      const streetId = item.street_id;
      const location = { lat: item.latitude, lng: item.longitude };
      const status = this.getStatusFromCI(item.congestion_index);

      let buffer = this.historyBuffer.get(streetId);
      if (!buffer) {
        buffer = { speeds: [], counts: [] };
        this.historyBuffer.set(streetId, buffer);
      }

      buffer.speeds.push(Math.floor(item.average_speed_kph));
      buffer.counts.push(item.vehicle_count);

      if (buffer.speeds.length > 20) buffer.speeds.shift();
      if (buffer.counts.length > 20) buffer.counts.shift();

      newData.set(streetId, {
        sensorId: streetId,
        timestamp: new Date(item.timestamp_utc),
        avgSpeed: Math.floor(item.average_speed_kph),
        vehicleCount: item.vehicle_count,
        congestionIndex: item.congestion_index,
        status,
        history: [...buffer.speeds],
        vehicleHistory: [...buffer.counts],
        name: item.street_name,
        location: location,
        description: `Traffic data for ${item.street_name}`,
        speedLimit: item.speed_limit_kph
      });
    });

    this.trafficState.next(newData);
  }

  private getStatusFromCI(ci: number): 'free' | 'dense' | 'near_capacity' | 'congested' {
    if (ci <= 0.2) return 'free';
    if (ci <= 0.5) return 'dense';
    if (ci <= 2.0) return 'near_capacity';
    return 'congested';
  }

  private startMockSimulation(): void {
    this.mockInterval = setInterval(() => {
      this.generateMockData();
    }, environment.pollingIntervalMs);
  }

  private generateMockData(): void {
    const newData = new Map<string, TrafficData>();

    this.sensors.forEach(sensor => {
      const isRushHour = Math.random() > 0.6;
      const baseSpeed = isRushHour ? 20 : 70;
      const randomVariation = (Math.random() * 20) - 10;

      let avgSpeed = Math.max(0, Math.min(100, baseSpeed + randomVariation));
      let vehicleCount = isRushHour
        ? Math.floor(Math.random() * 100) + 50
        : Math.floor(Math.random() * 20) + 5;

      const freeFlow = 80;
      const ci = avgSpeed > 0 ? (freeFlow - avgSpeed) / avgSpeed : 5.0;
      const status = this.getStatusFromCI(ci);
      const finalAvgSpeed = Math.floor(avgSpeed);

      let buffer = this.historyBuffer.get(sensor.id);
      if (!buffer) {
        buffer = { speeds: [], counts: [] };
        this.historyBuffer.set(sensor.id, buffer);
      }

      buffer.speeds.push(finalAvgSpeed);
      buffer.counts.push(vehicleCount);
      if (buffer.speeds.length > 20) buffer.speeds.shift();
      if (buffer.counts.length > 20) buffer.counts.shift();

      newData.set(sensor.id, {
        sensorId: sensor.id,
        timestamp: new Date(),
        avgSpeed: finalAvgSpeed,
        vehicleCount,
        congestionIndex: parseFloat(ci.toFixed(2)),
        status,
        history: [...buffer.speeds],
        vehicleHistory: [...buffer.counts],
        name: sensor.name,
        location: sensor.location,
        description: sensor.description,
        speedLimit: 80
      });
    });

    this.trafficState.next(newData);
  }
}
