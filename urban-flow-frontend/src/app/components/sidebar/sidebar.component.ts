import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TrafficService, Sensor, TrafficData } from '../../services/traffic.service';
import { Subscription } from 'rxjs';
import { trigger, transition, style, animate, keyframes } from '@angular/animations';
import { AlertService, Alert } from '../../services/alert.service';

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
          style({ transform: 'scale(1.1)', color: '#00ff9d', offset: 0.5 }),
          style({ transform: 'scale(1)', offset: 1 })
        ]))
      ]),
      transition(':decrement', [
        animate('300ms ease-out', keyframes([
          style({ transform: 'scale(1)', offset: 0 }),
          style({ transform: 'scale(1.1)', color: '#ff5252', offset: 0.5 }),
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
  sensorAlerts: Alert[] = [];

  private dataSub: Subscription | undefined;

  constructor(
    private trafficService: TrafficService,
    private alertService: AlertService
  ) {}

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
      this.sensorAlerts = [];
      return;
    }

    if (this.dataSub) this.dataSub.unsubscribe();

    this.dataSub = this.trafficService.trafficData$.subscribe(map => {
      if (this.selectedSensorId) {
        this.currentData = map.get(this.selectedSensorId);

        if (this.currentData) {
          this.selectedSensor = {
            id: this.currentData.sensorId,
            name: this.currentData.name,
            location: this.currentData.location,
            description: this.currentData.description || ''
          };
        }
      }
    });

    this.alertService.getAlertsForSensor(this.selectedSensorId).subscribe(alerts => {
      this.sensorAlerts = alerts;
    });
  }

  get congestionLevel(): string {
    return this.currentData?.status || 'unknown';
  }

  get congestionColor(): string {
    switch (this.currentData?.status) {
      case 'free': return 'var(--color-success)';
      case 'dense': return 'var(--color-warning)';
      case 'near_capacity': return '#ff9100';
      case 'congested': return 'var(--color-critical)';
      default: return 'var(--color-text-secondary)';
    }
  }

  getSparklinePath(data: number[] | undefined, maxVal: number = 100): string {
    if (!data || data.length < 2) return '';

    const width = 100;
    const height = 30;
    const min = 0;
    const padding = 2;
    const effectiveWidth = width - (2 * padding);

    return data.map((val, i) => {
      const x = padding + (i * (effectiveWidth / (data.length - 1)));
      const y = height - ((val - min) / (maxVal - min)) * height;
      return `${i === 0 ? 'M' : 'L'} ${x},${y}`;
    }).join(' ');
  }
}
