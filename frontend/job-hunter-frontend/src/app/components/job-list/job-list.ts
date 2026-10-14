import { CommonModule } from '@angular/common';
import { Component, computed, inject, output } from '@angular/core';
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

  protected readonly page = this.jobService.page;
  protected readonly totalPages = this.jobService.totalPages;
  protected readonly totalResults = this.jobService.totalResults;
  protected readonly hasNextPage = this.jobService.hasNextPage;
  protected readonly hasPreviousPage = this.jobService.hasPreviousPage;

  protected readonly rangeStart = computed(() =>
    this.totalResults() === 0 ? 0 : (this.page() - 1) * this.jobService.pageSize() + 1
  );
  protected readonly rangeEnd = computed(
    () => (this.page() - 1) * this.jobService.pageSize() + this.jobs().length
  );

  /** Windowed page numbers (max 5) centered on the current page. */
  protected readonly pageNumbers = computed(() => {
    const lastPage = this.totalPages();
    if (lastPage <= 1) return [];
    const windowSize = 5;
    const currentPage = this.page();
    let start = Math.max(1, currentPage - Math.floor(windowSize / 2));
    const end = Math.min(lastPage, start + windowSize - 1);
    start = Math.max(1, end - windowSize + 1);
    const pages: number[] = [];
    for (let candidate = start; candidate <= end; candidate++) {
      pages.push(candidate);
    }
    return pages;
  });

  protected onSelect(job: JobModel): void {
    this.jobService.selectJob(job);
    this.jobSelected.emit(job);
  }

  protected goToPage(page: number): void {
    this.jobService.goToPage(page);
  }

  protected previousPage(): void {
    this.jobService.previousPage();
  }

  protected nextPage(): void {
    this.jobService.nextPage();
  }

  protected formatScorePercentage(score?: number): number {
    if (score == null) return 0;
    return Math.round(score * 100);
  }

  /**
   * Determines the recommendation tier for visual styling:
   * - 'apply': High match / top-tier opportunity
   * - 'consider': Neutral / moderate match indicator
   * - 'skip': Low match / recedes into background
   */
  protected getRecommendationTier(job: JobModel): 'apply' | 'consider' | 'skip' | null {
    const rec = job.recommendation?.trim().toUpperCase();
    if (rec) {
      if (rec.includes('APPLY') || rec.includes('HIGH MATCH') || rec.includes('RECOMMENDED')) {
        return 'apply';
      }
      if (rec.includes('CONSIDER')) {
        return 'consider';
      }
      if (rec.includes('SKIP')) {
        return 'skip';
      }
    }

    // Fallback based on score (0-100) or match_score (0.00-1.00)
    if (job.score != null) {
      if (job.score >= 80) return 'apply';
      if (job.score >= 60) return 'consider';
      return 'skip';
    }

    if (job.match_score != null) {
      const pct = this.formatScorePercentage(job.match_score);
      if (pct >= 80) return 'apply';
      if (pct >= 60) return 'consider';
      return 'skip';
    }

    return null;
  }

  /**
   * Returns human-readable label for the status tag.
   */
  protected getRecommendationLabel(job: JobModel): string | null {
    const raw = job.recommendation?.trim().toUpperCase();
    if (raw) {
      if (raw.includes('APPLY')) return 'APPLY';
      if (raw.includes('HIGH MATCH')) return 'HIGH MATCH';
      if (raw.includes('CONSIDER')) return 'CONSIDER';
      if (raw.includes('SKIP')) return 'SKIP';
      return raw;
    }

    const tier = this.getRecommendationTier(job);
    if (tier === 'apply') return 'HIGH MATCH';
    if (tier === 'consider') return 'CONSIDER';
    if (tier === 'skip') return 'SKIP';
    return null;
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

