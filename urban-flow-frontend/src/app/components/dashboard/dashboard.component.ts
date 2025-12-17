import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MapComponent } from '../map/map.component';
import { SidebarComponent } from '../sidebar/sidebar.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MapComponent, SidebarComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {
  selectedSensorId: string | null = null;

  onSensorSelected(sensorId: string): void {
    console.log('Sensor Selected:', sensorId);
    this.selectedSensorId = sensorId;
  }

  onSidebarClosed(): void {
    this.selectedSensorId = null;
  }
}
