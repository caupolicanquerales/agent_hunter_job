import { CommonModule } from '@angular/common';
import { Component, ElementRef, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { JobModel, JobSortOption } from '../../models/job.model';
import { JobService } from '../../services/job.service';
import { JobDetail } from '../job-detail/job-detail';
import { JobList } from '../job-list/job-list';

@Component({
  selector: 'app-job-dashboard',
  imports: [CommonModule, FormsModule, JobList, JobDetail],
  templateUrl: './job-dashboard.html',
  styleUrl: './job-dashboard.scss',
})
export class JobDashboard {
  protected readonly jobService = inject(JobService);
  protected readonly skillsDropdownOpen = signal<boolean>(false);
  protected readonly mobileFiltersOpen = signal<boolean>(false);
  protected readonly activeMobileTab = signal<'list' | 'detail'>('list');

  // Quick access to service signals
  protected readonly filteredJobs = this.jobService.filteredJobs;
  protected readonly selectedJob = this.jobService.selectedJob;
  protected readonly availableSkills = this.jobService.availableSkills;
  protected readonly filters = this.jobService.filters;
  protected readonly totalMatches = this.jobService.totalMatches;
  protected readonly averageMatchPercentage = this.jobService.averageMatchPercentage;

  constructor(private elementRef: ElementRef) {}

  protected onKeywordChange(value: string): void {
    this.jobService.setKeyword(value);
  }

  protected onRemoteToggle(): void {
    this.jobService.setRemoteOnly(!this.filters().remoteOnly);
  }

  protected toggleSkillsDropdown(): void {
    this.skillsDropdownOpen.update((open) => !open);
  }

  protected toggleMobileFilters(): void {
    this.mobileFiltersOpen.update((open) => !open);
  }

  protected switchMobileTab(tab: 'list' | 'detail'): void {
    this.activeMobileTab.set(tab);
  }

  protected onJobSelectedFromList(): void {
    // On mobile viewports, automatically switch tab to detail when a job is chosen
    this.activeMobileTab.set('detail');
  }

  protected onSkillToggle(skill: string): void {
    this.jobService.toggleSkill(skill);
  }

  protected isSkillSelected(skill: string): boolean {
    return this.filters().selectedSkills.includes(skill);
  }

  protected removeSkill(skill: string): void {
    this.jobService.removeSkill(skill);
  }

  protected clearAllSkills(): void {
    this.jobService.clearSkills();
  }

  protected onSortChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.jobService.setSortBy(target.value as JobSortOption);
  }

  protected resetFilters(): void {
    this.jobService.resetFilters();
  }

  @HostListener('document:click', ['$event'])
  protected onDocumentClick(event: MouseEvent): void {
    const clickedInside = this.elementRef.nativeElement.querySelector('.skills-dropdown-container')?.contains(event.target as Node);
    if (!clickedInside && this.skillsDropdownOpen()) {
      this.skillsDropdownOpen.set(false);
    }
  }
}

