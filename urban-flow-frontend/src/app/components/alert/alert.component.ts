import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common'; // Import CommonModule for *ngIf
import { Subscription } from 'rxjs';
import { AlertService, Alert } from '../../services/alert.service'; // Updated import
import { environment } from '../../config/api.config';

@Component({
  selector: 'app-alert',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './alert.component.html',
  styleUrls: ['./alert.component.css']
})
export class AlertComponent implements OnInit, OnDestroy {
  currentAlert: Alert | null = null;
  private sub: Subscription | null = null;
  private timeoutId: any;

  constructor(private alertService: AlertService) {} // Updated injection

  ngOnInit(): void {
    // Polling starts automatically in the service constructor
    this.sub = this.alertService.alerts$.subscribe(alert => {
      this.showAlert(alert);
    });
  }

  ngOnDestroy(): void {
    if (this.sub) this.sub.unsubscribe();
  }

  showAlert(alert: Alert) {
    this.currentAlert = alert;
    
    // Auto-dismiss after 10 seconds
    if (this.timeoutId) clearTimeout(this.timeoutId);
    this.timeoutId = setTimeout(() => {
      this.currentAlert = null;
    }, 10000);
  }

  dismiss() {
    this.currentAlert = null;
    if (this.timeoutId) clearTimeout(this.timeoutId);
  }

  zoomToLocation() {
    if (this.currentAlert) {
      console.log('Zoom to:', this.currentAlert.location);
      const event = new CustomEvent('urbanflow:zoom', { detail: this.currentAlert.location });
      window.dispatchEvent(event);
    }
  }
}
