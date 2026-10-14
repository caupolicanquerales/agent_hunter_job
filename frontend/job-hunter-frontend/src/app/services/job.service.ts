import { Injectable, computed, inject, signal } from '@angular/core';
import { catchError, debounceTime, merge, of, Subject, switchMap } from 'rxjs';
import { JobFilterCriteria, JobModel, JobSortOption } from '../models/job.model';
import { JobSearchResponse, toJobModel } from '../models/scraped-job-posting.model';
import { JobSearchParams, SseService } from './sse.service';

const DEFAULT_SEARCH_QUERY = 'developer';
const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;
const SEARCH_DEBOUNCE_MS = 300;

@Injectable({
  providedIn: 'root'
})
export class JobService {
  private readonly sseService = inject(SseService);
  private readonly searchRequest$ = new Subject<void>();
  private readonly pageRequest$ = new Subject<void>();

  private readonly _jobs = signal<JobModel[]>([]);
  private readonly _selectedJobId = signal<string | null>(null);
  private readonly _page = signal(1);
  private readonly _pageSize = signal(DEFAULT_PAGE_SIZE);
  private readonly _totalResults = signal(0);
  private readonly _totalPages = signal(0);
  private readonly _filters = signal<JobFilterCriteria>({
    keyword: '',
    remoteOnly: false,
    selectedSkills: [],
    sortBy: 'match_score_desc'
  });

  // Public read-only signals
  public readonly jobs = this._jobs.asReadonly();
  public readonly selectedJobId = this._selectedJobId.asReadonly();
  public readonly filters = this._filters.asReadonly();
  public readonly page = this._page.asReadonly();
  public readonly pageSize = this._pageSize.asReadonly();
  public readonly totalResults = this._totalResults.asReadonly();
  public readonly totalPages = this._totalPages.asReadonly();
  public readonly hasNextPage = computed(() => this._page() < this._totalPages());
  public readonly hasPreviousPage = computed(() => this._page() > 1);

  constructor() {
    merge(
      this.searchRequest$.pipe(debounceTime(SEARCH_DEBOUNCE_MS)),
      this.pageRequest$
    )
      .pipe(
        switchMap(() =>
          this.sseService
            .getJobs<JobSearchResponse>(this.buildSearchParams())
            .pipe(catchError(() => of(null)))
        )
      )
      .subscribe((response) => {
        if (response) {
          this.applyPagination(response);
          this.loadJobs(response.results.map(toJobModel));
        }
      });
  }

  // All unique available skills extracted from current jobs
  public readonly availableSkills = computed(() => {
    const skillSet = new Set<string>();
    for (const job of this._jobs()) {
      for (const skill of job.required_skills) {
        if (skill?.trim()) {
          skillSet.add(skill.trim());
        }
      }
    }
    return Array.from(skillSet).sort((a, b) => a.localeCompare(b));
  });

  // Filtered and sorted jobs based on real-time criteria
  public readonly filteredJobs = computed(() => {
    const list = this._jobs();
    const criteria = this._filters();
    const query = criteria.keyword.trim().toLowerCase();

    return list
      .filter((job) => {
        // Remote toggle filter
        if (criteria.remoteOnly && !job.is_remote) {
          return false;
        }

        // Skills filter
        if (criteria.selectedSkills.length > 0) {
          const jobSkillsLower = job.required_skills.map((s) => s.toLowerCase());
          const hasSelectedSkill = criteria.selectedSkills.some((s) =>
            jobSkillsLower.includes(s.toLowerCase())
          );
          if (!hasSelectedSkill) {
            return false;
          }
        }

        // Keyword search across title, company, location, skills, and clean_description
        if (query) {
          const matchTitle = job.title.toLowerCase().includes(query);
          const matchCompany = job.company.toLowerCase().includes(query);
          const matchLocation = job.location.toLowerCase().includes(query);
          const matchSkills = job.required_skills.some((s) => s.toLowerCase().includes(query));
          const matchDesc = job.clean_description.toLowerCase().includes(query);

          if (!matchTitle && !matchCompany && !matchLocation && !matchSkills && !matchDesc) {
            return false;
          }
        }

        return true;
      })
      .sort((a, b) => {
        switch (criteria.sortBy) {
          case 'match_score_desc':
            return (b.match_score ?? 0) - (a.match_score ?? 0);
          case 'match_score_asc':
            return (a.match_score ?? 0) - (b.match_score ?? 0);
          case 'date_desc':
            return new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime();
          case 'title_asc':
            return a.title.localeCompare(b.title);
          default:
            return 0;
        }
      });
  });

  // Active selected job; falls back to first visible item if current selection is filtered out
  public readonly selectedJob = computed(() => {
    const currentId = this._selectedJobId();
    const currentFiltered = this.filteredJobs();

    if (currentId) {
      const match = currentFiltered.find((j) => j.id === currentId);
      if (match) return match;
    }

    return currentFiltered.length > 0 ? currentFiltered[0] : null;
  });

  // Computed metrics
  public readonly totalMatches = computed(() => this.filteredJobs().length);
  public readonly averageMatchPercentage = computed(() => {
    const list = this.filteredJobs();
    if (!list.length) return 0;
    const total = list.reduce((sum, item) => sum + (item.match_score ?? 0), 0);
    return Math.round((total / list.length) * 100);
  });

  // Action methods
  public selectJob(jobOrId: JobModel | string): void {
    const id = typeof jobOrId === 'string' ? jobOrId : jobOrId.id ?? null;
    this._selectedJobId.set(id);
  }

  public setKeyword(keyword: string): void {
    this._filters.update((prev) => ({ ...prev, keyword }));
    this._page.set(1);
    this.requestJobs();
  }

  /** Requests a fresh search from the backend using the current keyword. */
  public requestJobs(): void {
    this.searchRequest$.next();
  }

  /** Jumps to an absolute page (clamped to the available range) and reloads. */
  public goToPage(page: number): void {
    const target = this.clampPage(page);
    if (target === this._page()) return;
    this._page.set(target);
    this.pageRequest$.next();
  }

  /** Loads the next page when one is available. */
  public nextPage(): void {
    if (this.hasNextPage()) {
      this.goToPage(this._page() + 1);
    }
  }

  /** Loads the previous page when one is available. */
  public previousPage(): void {
    if (this.hasPreviousPage()) {
      this.goToPage(this._page() - 1);
    }
  }

  /** Changes the page size, resetting to the first page. */
  public setPageSize(pageSize: number): void {
    const size = Math.max(1, Math.min(Math.trunc(pageSize) || DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE));
    if (size === this._pageSize()) return;
    this._pageSize.set(size);
    this._page.set(1);
    this.pageRequest$.next();
  }

  public setRemoteOnly(remoteOnly: boolean): void {
    this._filters.update((prev) => ({ ...prev, remoteOnly }));
  }

  public toggleSkill(skill: string): void {
    this._filters.update((prev) => {
      const exists = prev.selectedSkills.includes(skill);
      const nextSkills = exists
        ? prev.selectedSkills.filter((s) => s !== skill)
        : [...prev.selectedSkills, skill];
      return { ...prev, selectedSkills: nextSkills };
    });
  }

  public removeSkill(skill: string): void {
    this._filters.update((prev) => ({
      ...prev,
      selectedSkills: prev.selectedSkills.filter((s) => s !== skill)
    }));
  }

  public clearSkills(): void {
    this._filters.update((prev) => ({ ...prev, selectedSkills: [] }));
  }

  public setSortBy(sortBy: JobSortOption): void {
    this._filters.update((prev) => ({ ...prev, sortBy }));
  }

  public resetFilters(): void {
    this._filters.set({
      keyword: '',
      remoteOnly: false,
      selectedSkills: [],
      sortBy: 'match_score_desc'
    });
    this._page.set(1);
    this.requestJobs();
  }

  private buildSearchParams(): JobSearchParams {
    const keyword = this._filters().keyword.trim();
    return {
      query: keyword || DEFAULT_SEARCH_QUERY,
      page: this._page(),
      page_size: this._pageSize()
    };
  }

  private applyPagination(response: JobSearchResponse): void {
    this._page.set(response.page);
    this._pageSize.set(response.page_size);
    this._totalResults.set(response.total_results);
    this._totalPages.set(response.total_pages);
  }

  private clampPage(page: number): number {
    const lastPage = Math.max(1, this._totalPages());
    return Math.min(Math.max(1, Math.trunc(page) || 1), lastPage);
  }

  public loadJobs(jobs: JobModel[]): void {
    this._jobs.set(jobs);
    if (jobs.length > 0) {
      this._selectedJobId.set(jobs[0].id ?? null);
    } else {
      this._selectedJobId.set(null);
    }
  }
}
