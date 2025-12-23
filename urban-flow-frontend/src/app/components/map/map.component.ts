import { Component, OnInit, Output, EventEmitter, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import * as L from 'leaflet';

import { TrafficService, Sensor, TrafficData } from '../../services/traffic.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [],
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit, OnDestroy {
  @Output() sensorSelected = new EventEmitter<string>();

  private map: L.Map | undefined;
  private markers: Map<string, L.Marker> = new Map();
  private trafficSub: Subscription | undefined;
  private isBrowser: boolean;

  private currentTrafficData: Map<string, TrafficData> = new Map();

  constructor(
    private trafficService: TrafficService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  ngOnInit(): void {
    if (this.isBrowser) {
      this.initMap();
      this.subscribeToTraffic();
    }
  }

  ngOnDestroy(): void {
    if (this.trafficSub) {
      this.trafficSub.unsubscribe();
    }
    if (this.map) {
      this.map.remove();
      this.map = undefined;
    }
  }

  private initMap(): void {
    // Safety check for HMR
    if (this.map) {
        this.map.remove();
    }

    // Center on Vienna
    this.map = L.map('map', {
      zoomControl: false, // Custom placement if needed, or default
      attributionControl: false
    }).setView([48.2082, 16.3738], 13); // Vienna Center

    // Dark Matter Tile Layer (Premium look)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(this.map);

    // ... markers added later or by filter ...
    // Note: initMap doesn't add markers directly anymore because subscribeToTraffic/filter handles it?
    // Wait, previous code added sensors in initMap.
    // We should keep that behavior or ensure filter runs. 
    // The previous code had:
    const sensors = this.trafficService.getSensors();
    sensors.forEach(sensor => {
      const marker = L.marker([sensor.location.lat, sensor.location.lng], {
        icon: this.createCustomIcon('free'), // Default state
        title: sensor.name,
        alt: `Sensor at ${sensor.name}`
      }).addTo(this.map!)
        .bindTooltip(`
          <div class="custom-tooltip-content">
            <div class="tooltip-title">${sensor.name}</div>
            <div class="tooltip-desc">${sensor.description}</div>
            <div class="tooltip-click-hint">Click for details</div>
          </div>
        `, {
          className: 'custom-tooltip',
          direction: 'top',
          offset: [0, -12],
          opacity: 1
        });

      marker.on('click', () => {
        this.sensorSelected.emit(sensor.id);
      });

      this.markers.set(sensor.id, marker);
    });
  }

  private currentSearchTerm = '';
  private currentActiveStatuses: string[] = [];

  // Public API for Dashboard Filter
  filterSensors(searchTerm: string, activeStatuses: string[]): void {
      this.currentSearchTerm = searchTerm.toLowerCase();
      this.currentActiveStatuses = activeStatuses;
      this.applyFilters();
  }

  private applyFilters(): void {
      this.markers.forEach((marker, sensorId) => {
          this.updateMarkerVisibility(sensorId, marker);
      });
  }

  private updateMarkerVisibility(sensorId: string, marker: L.Marker): void {
      const sensor = this.trafficService.getSensors().find(s => s.id === sensorId);
      const data = this.currentTrafficData.get(sensorId);
      
      if (!sensor) return;

      const matchesSearch = sensor.name.toLowerCase().includes(this.currentSearchTerm) || 
                            sensor.description.toLowerCase().includes(this.currentSearchTerm);
      
      const status = data?.status || 'free'; 
      const matchesStatus = this.currentActiveStatuses.length === 0 || this.currentActiveStatuses.includes(status);

      if (matchesSearch && matchesStatus) {
          if (!this.map?.hasLayer(marker)) {
              marker.addTo(this.map!);
          }
      } else {
          if (this.map?.hasLayer(marker)) {
              this.map?.removeLayer(marker);
          }
      }
  }

  private subscribeToTraffic(): void {
    this.trafficSub = this.trafficService.trafficData$.subscribe(dataMap => {
        this.currentTrafficData = dataMap;
        
        // Update Markers and re-apply filter logic
        this.markers.forEach((marker, sensorId) => {
            const data = dataMap.get(sensorId);
            if (data) {
                const newIcon = this.createCustomIcon(data.status);
                marker.setIcon(newIcon);
                // Re-evaluate visibility because status (which affects filtering) might have changed
                this.updateMarkerVisibility(sensorId, marker);
            }
        });
    });
  }

  private createCustomIcon(status: 'free' | 'dense' | 'near_capacity' | 'congested'): L.DivIcon {
    let colorClass = '';
    switch (status) {
      case 'free': colorClass = 'status-free'; break;
      case 'dense': colorClass = 'status-dense'; break;
      case 'near_capacity': colorClass = 'status-warning'; break;
      case 'congested': colorClass = 'status-critical'; break;
    }

    return L.divIcon({
      className: 'custom-pin', // defined in component scss
      html: `<div class="pin-glow ${colorClass}"></div><div class="pin-core"></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
  }
}
