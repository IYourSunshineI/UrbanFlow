import { Component, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common'; // Important for ngClass etc
import { FormsModule } from '@angular/forms'; // For input binding if using ngModel

import { MapComponent } from '../map/map.component';
import { SidebarComponent } from '../sidebar/sidebar.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, MapComponent, SidebarComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {
  @ViewChild(MapComponent) mapComponent!: MapComponent;
  
  selectedSensorId: string | null = null;
  searchTerm: string = '';
  
  // Status Filters
  filterStatuses: { id: string, label: string, active: boolean, color: string }[] = [
      { id: 'free', label: 'Free', active: true, color: 'var(--color-success)' },
      { id: 'dense', label: 'Dense', active: true, color: 'var(--color-warning)' },
      { id: 'near_capacity', label: 'Heavy', active: true, color: '#ff9100' },
      { id: 'congested', label: 'Jam', active: true, color: 'var(--color-critical)' }
  ];

  onSensorSelected(sensorId: string): void {
    console.log('Sensor Selected:', sensorId);
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
