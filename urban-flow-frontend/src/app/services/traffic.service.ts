import { Injectable } from '@angular/core';
import { BehaviorSubject, interval, map, Observable, shareReplay } from 'rxjs';

export interface Sensor {
  id: string;
  name: string;
  location: { lat: number; lng: number };
  description: string;
}

export interface TrafficData {
  sensorId: string;
  timestamp: Date;
  avgSpeed: number; // km/h
  vehicleCount: number; // per interval
  congestionIndex: number; // CI
  status: 'free' | 'dense' | 'near_capacity' | 'congested';
}

@Injectable({
  providedIn: 'root'
})
export class TrafficService {

  // Mock Sensors (Vienna)
  private sensors: Sensor[] = [
    { id: 'S001', name: 'A23 Südosttangente / Praterbrücke', location: { lat: 48.205, lng: 16.425 }, description: 'High volume commuter route' },
    { id: 'S002', name: 'B1 Wiener Straße / Schönbrunn', location: { lat: 48.185, lng: 16.320 }, description: 'Tourist and local traffic' },
    { id: 'S003', name: 'Ringstraße / Oper', location: { lat: 48.202, lng: 16.369 }, description: 'City center loop' },
    { id: 'S004', name: 'Gürtel / Westbahnhof', location: { lat: 48.196, lng: 16.338 }, description: 'Major urban arterial' },
    { id: 'S005', name: 'Donauufer Autobahn (A22)', location: { lat: 48.235, lng: 16.400 }, description: 'Northern connector' },
    { id: 'S006', name: 'Handelskai', location: { lat: 48.230, lng: 16.380 }, description: 'Riverbank commercial route' }
  ];

  // Store latest data for each sensor
  private trafficState = new BehaviorSubject<Map<string, TrafficData>>(new Map());
  
  public trafficData$ = this.trafficState.asObservable();

  constructor() {
    this.startSimulation();
  }

  getSensors(): Sensor[] {
    return this.sensors;
  }

  private startSimulation() {
    // Update every 3 seconds to show movement
    interval(3000).subscribe(() => {
      const newData = new Map<string, TrafficData>();
      
      this.sensors.forEach(sensor => {
        // Randomize mock data
        const isRushHour = Math.random() > 0.6; // Simulate burstiness
        const baseSpeed = isRushHour ? 20 : 70;
        const randomVariation = (Math.random() * 20) - 10;
        
        let avgSpeed = Math.max(0, Math.min(100, baseSpeed + randomVariation));
        let vehicleCount = isRushHour ? Math.floor(Math.random() * 100) + 50 : Math.floor(Math.random() * 20) + 5;
        
        // Calculate Congestion Index roughly: (FreeFlow - Avg) / Avg
        // Assume FreeFlow ~ 80km/h
        const freeFlow = 80;
        const ci = avgSpeed > 0 ? (freeFlow - avgSpeed) / avgSpeed : 5.0; 
        
        let status: 'free' | 'dense' | 'near_capacity' | 'congested';
        if (ci <= 0.2) status = 'free';
        else if (ci <= 0.5) status = 'dense';
        else if (ci <= 2.0) status = 'near_capacity';
        else status = 'congested';

        newData.set(sensor.id, {
          sensorId: sensor.id,
          timestamp: new Date(),
          avgSpeed: Math.floor(avgSpeed),
          vehicleCount,
          congestionIndex: parseFloat(ci.toFixed(2)),
          status
        });
      });

      this.trafficState.next(newData);
    });
  }
}
