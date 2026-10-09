import { Routes } from '@angular/router';
import { JobDashboard } from './components/job-dashboard/job-dashboard';

export const routes: Routes = [
  {
    path: '',
    component: JobDashboard,
    title: 'Agent Hunter - Job Opportunities Dashboard'
  },
  {
    path: '**',
    redirectTo: ''
  }
];

