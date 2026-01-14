import { Component } from '@angular/core';

import { DashboardComponent } from './components/dashboard/dashboard.component';
import { AlertComponent } from './components/alert/alert.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [DashboardComponent, AlertComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'urban-flow-frontend';
}
