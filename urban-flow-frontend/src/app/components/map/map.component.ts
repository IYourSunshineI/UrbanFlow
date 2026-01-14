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
    // Markers will be added dynamically when traffic data arrives
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
      const data = this.currentTrafficData.get(sensorId);
      
      if (!data) return;

      // Filter by Search Term
      const matchesSearch = data.name.toLowerCase().includes(this.currentSearchTerm) || 
                            (data.description && data.description.toLowerCase().includes(this.currentSearchTerm));
      
      // Filter by Status
      const status = data.status || 'free'; 
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

        // Iterate over traffic data to update/create markers
        dataMap.forEach((data, sensorId) => {
             let marker = this.markers.get(sensorId);

             // Create marker if it doesn't exist
             if (!marker) {
                 marker = L.marker([data.location.lat, data.location.lng], {
                    title: data.name,
                    alt: `Sensor at ${data.name}`
                 }).addTo(this.map!);

                 marker.bindTooltip(`
                  <div class="custom-tooltip-content">
                    <div class="tooltip-title">${data.name}</div>
                    <div class="tooltip-desc">${data.description}</div>
                    <div class="tooltip-click-hint">Click for details</div>
                  </div>
                `, {
                  className: 'custom-tooltip',
                  direction: 'top',
                  offset: [0, -12],
                  opacity: 1
                });

                marker.on('click', () => {
                   this.sensorSelected.emit(sensorId);
                });

                this.markers.set(sensorId, marker);
             }

             // Update Icon based on status
             const newIcon = this.createCustomIcon(data.status);
             marker.setIcon(newIcon);

             // Apply filters
             this.updateMarkerVisibility(sensorId, marker);
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


  flyToSensor(sensorId: string): void {
      const marker = this.markers.get(sensorId);
      if (marker && this.map) {
          // Open Sidebar logic is handled by Dashboard, map just zooms
          this.map.flyTo(marker.getLatLng(), 15, {
              animate: true,
              duration: 1.5
          });
          
          // Optional: Open popup or highlight
          // marker.openPopup(); 
      } else {
          console.warn(`Marker for sensor ${sensorId} not found in map.`);
      }
  }
}
