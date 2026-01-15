import { Component, ViewChild, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MapComponent } from '../map/map.component';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { AlertService } from '../../services/alert.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, MapComponent, SidebarComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  @ViewChild(MapComponent) mapComponent!: MapComponent;

  selectedSensorId: string | null = null;
  searchTerm: string = '';
  private alertSub: Subscription | undefined;

  filterStatuses: { id: string; label: string; active: boolean; color: string }[] = [
    { id: 'free', label: 'Free', active: true, color: 'var(--color-success)' },
    { id: 'dense', label: 'Dense', active: true, color: 'var(--color-warning)' },
    { id: 'near_capacity', label: 'Heavy', active: true, color: '#ff9100' },
    { id: 'congested', label: 'Jam', active: true, color: 'var(--color-critical)' }
  ];

  constructor(private alertService: AlertService) {}

  ngOnInit(): void {
    this.alertSub = this.alertService.alertSelected$.subscribe(alert => {
      if (alert.sensor_id) {
        this.onSensorSelected(alert.sensor_id);
        this.mapComponent.flyToSensor(alert.sensor_id);
      }
    });
  }

  ngOnDestroy(): void {
    if (this.alertSub) this.alertSub.unsubscribe();
  }

  onSensorSelected(sensorId: string): void {
    this.selectedSensorId = sensorId;
  }

  onSidebarClosed(): void {
    this.selectedSensorId = null;
  }

  updateFilter(): void {
    const activeStats = this.filterStatuses.filter(s => s.active).map(s => s.id);
    this.mapComponent.filterSensors(this.searchTerm, activeStats);
  }

  toggleStatus(statusId: string): void {
    const status = this.filterStatuses.find(s => s.id === statusId);
    if (status) {
      status.active = !status.active;
      this.updateFilter();
    }
  }
}
