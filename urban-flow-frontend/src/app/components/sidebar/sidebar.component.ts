import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TrafficService, Sensor, TrafficData } from '../../services/traffic.service';
import { Subscription } from 'rxjs';
import { trigger, transition, style, animate, keyframes } from '@angular/animations';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss'],
  animations: [
    trigger('valueChange', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ]),
      transition(':increment', [
        animate('300ms ease-out', keyframes([
          style({ transform: 'scale(1)', offset: 0 }),
          style({ transform: 'scale(1.1)', color: '#00ff9d', offset: 0.5 }), // Green flash on up
          style({ transform: 'scale(1)', offset: 1 })
        ]))
      ]),
      transition(':decrement', [
        animate('300ms ease-out', keyframes([
          style({ transform: 'scale(1)', offset: 0 }),
          style({ transform: 'scale(1.1)', color: '#ff5252', offset: 0.5 }), // Red flash on down
          style({ transform: 'scale(1)', offset: 1 })
        ]))
      ])
    ])
  ]
})
export class SidebarComponent implements OnChanges, OnDestroy {
  @Input() selectedSensorId: string | null = null;
  @Output() close = new EventEmitter<void>();

  selectedSensor: Sensor | undefined;
  currentData: TrafficData | undefined;
  
  private dataSub: Subscription | undefined;

  constructor(private trafficService: TrafficService) {}

  ngOnChanges(changes: SimpleChanges): void {
      if (changes['selectedSensorId']) {
          this.updateSelection();
      }
  }

  ngOnDestroy(): void {
      if (this.dataSub) {
          this.dataSub.unsubscribe();
      }
  }

  closeSidebar(): void {
      this.close.emit();
  }

  private updateSelection(): void {
      if (!this.selectedSensorId) {
          this.selectedSensor = undefined;
          this.currentData = undefined;
          return;
      }

      // Find static sensor info
      this.selectedSensor = this.trafficService.getSensors().find(s => s.id === this.selectedSensorId);

      // Subscribe to real-time data for this sensor
      if (this.dataSub) this.dataSub.unsubscribe();
      
      this.dataSub = this.trafficService.trafficData$.subscribe(map => {
          if (this.selectedSensorId) {
              this.currentData = map.get(this.selectedSensorId);
          }
      });
  }

  get congestionLevel(): string {
      return this.currentData?.status || 'unknown';
  }

  get congestionColor(): string {
     switch(this.currentData?.status) {
         case 'free': return 'var(--color-success)';
         case 'dense': return 'var(--color-warning)';
         case 'near_capacity': return '#ff9100'; // Orange
         case 'congested': return 'var(--color-critical)';
         default: return 'var(--color-text-secondary)';
     }
  }
}
