import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { AlertService, Alert } from '../../services/alert.service';

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

  constructor(private alertService: AlertService) {}

  ngOnInit(): void {
    this.sub = this.alertService.alerts$.subscribe(alert => {
      this.showAlert(alert);
    });
  }

  ngOnDestroy(): void {
    if (this.sub) this.sub.unsubscribe();
  }

  showAlert(alert: Alert) {
    this.currentAlert = alert;

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
      this.alertService.selectAlert(this.currentAlert);
      this.dismiss();
    }
  }
}
