import { CommonModule } from '@angular/common';
import { Component, inject, output } from '@angular/core';
import { JobModel } from '../../models/job.model';
import { JobService } from '../../services/job.service';

@Component({
  selector: 'app-job-list',
  imports: [CommonModule],
  templateUrl: './job-list.html',
  styleUrl: './job-list.scss',
})
export class JobList {
  protected readonly jobService = inject(JobService);

  public readonly jobSelected = output<JobModel>();

  protected readonly jobs = this.jobService.filteredJobs;
  protected readonly selectedJob = this.jobService.selectedJob;
  protected readonly selectedJobId = this.jobService.selectedJobId;

  protected onSelect(job: JobModel): void {
    this.jobService.selectJob(job);
    this.jobSelected.emit(job);
  }

  protected formatScorePercentage(score?: number): number {
    if (score == null) return 0;
    return Math.round(score * 100);
  }

  protected getScoreBadgeClass(score?: number): string {
    const pct = this.formatScorePercentage(score);
    if (pct >= 90) return 'score-excellent';
    if (pct >= 80) return 'score-great';
    if (pct >= 70) return 'score-good';
    return 'score-neutral';
  }

  protected resetFilters(): void {
    this.jobService.resetFilters();
  }
}

