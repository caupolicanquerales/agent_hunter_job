import { CommonModule } from '@angular/common';
import { Component, computed, inject, output, viewChild } from '@angular/core';
import { JobModel } from '../../models/job.model';
import { JobService } from '../../services/job.service';
import { RawPayloadViewer } from '../raw-payload-viewer/raw-payload-viewer';

@Component({
  selector: 'app-job-detail',
  imports: [CommonModule, RawPayloadViewer],
  templateUrl: './job-detail.html',
  styleUrl: './job-detail.scss',
})
export class JobDetail {
  protected readonly jobService = inject(JobService);
  protected readonly payloadViewer = viewChild(RawPayloadViewer);

  public readonly backToList = output<void>();

  public readonly job = this.jobService.selectedJob;
  public readonly totalAvailableJobs = computed(() => this.jobService.jobs().length);
  public readonly filteredCount = this.jobService.totalMatches;

  // Formatted match score percentage
  protected readonly matchPercentage = computed(() => {
    const current = this.job();
    if (!current?.match_score) return 0;
    return Math.round(current.match_score * 100);
  });

  // External link / Apply URL if extracted in payload or attributes
  protected readonly externalUrl = computed(() => {
    const current = this.job();
    if (!current) return null;
    return (
      current.raw_payload?.attributes?.apply_url ||
      current.raw_payload?.url ||
      null
    );
  });

  // Format salary display if present
  protected readonly formattedSalary = computed(() => {
    const current = this.job();
    if (!current || (!current.salary_min && !current.salary_max)) return null;

    const currencySymbol = current.currency === 'EUR' ? '€' : '$';
    const min = current.salary_min ? `${currencySymbol}${current.salary_min.toLocaleString()}` : '';
    const max = current.salary_max ? `${currencySymbol}${current.salary_max.toLocaleString()}` : '';

    if (min && max) return `${min} - ${max} / year`;
    if (min) return `From ${min} / year`;
    if (max) return `Up to ${max} / year`;
    return null;
  });

  // Relative or formatted scraped date
  protected readonly formattedDate = computed(() => {
    const current = this.job();
    if (!current?.scraped_at) return '';
    try {
      const date = new Date(current.scraped_at);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return current.scraped_at;
    }
  });

  // Typography-focused HTML renderer for clean_description
  protected readonly formattedDescriptionHtml = computed(() => {
    const text = this.job()?.clean_description;
    if (!text) return '';
    return this.renderDescription(text);
  });

  protected onSkillClick(skill: string): void {
    this.jobService.toggleSkill(skill);
  }

  protected isSkillActiveInFilter(skill: string): boolean {
    return this.jobService.filters().selectedSkills.includes(skill);
  }

  protected getScoreConfidenceLabel(score?: number): string {
    const pct = score ? Math.round(score * 100) : 0;
    if (pct >= 90) return 'High Match';
    if (pct >= 80) return 'Strong Fit';
    if (pct >= 70) return 'Moderate Fit';
    return 'Low Alignment';
  }

  protected getScoreConfidenceClass(score?: number): string {
    const pct = score ? Math.round(score * 100) : 0;
    if (pct >= 90) return 'conf-high';
    if (pct >= 80) return 'conf-strong';
    if (pct >= 70) return 'conf-moderate';
    return 'conf-low';
  }

  protected jumpToRawPayload(): void {
    const viewer = this.payloadViewer();
    if (viewer) {
      viewer.openAccordion();
    }
    const el = document.getElementById('raw-payload-section');
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  protected resetFilters(): void {
    this.jobService.resetFilters();
  }

  private renderDescription(markdownText: string): string {
    const lines = markdownText.split('\n');
    const result: string[] = [];
    let inList = false;

    for (let rawLine of lines) {
      const line = rawLine.trim();

      // Heading 3
      if (line.startsWith('### ')) {
        if (inList) {
          result.push('</ul>');
          inList = false;
        }
        const headingContent = this.escapeAndFormatInline(line.substring(4));
        result.push(`<h3 class="desc-heading">${headingContent}</h3>`);
        continue;
      }

      // Heading 2
      if (line.startsWith('## ')) {
        if (inList) {
          result.push('</ul>');
          inList = false;
        }
        const headingContent = this.escapeAndFormatInline(line.substring(3));
        result.push(`<h2 class="desc-subheading">${headingContent}</h2>`);
        continue;
      }

      // Unordered list item
      if (line.startsWith('- ') || line.startsWith('* ')) {
        if (!inList) {
          result.push('<ul class="desc-list">');
          inList = true;
        }
        const itemContent = this.escapeAndFormatInline(line.substring(2));
        result.push(`<li class="desc-list-item">${itemContent}</li>`);
        continue;
      }

      // Blank line
      if (line === '') {
        if (inList) {
          result.push('</ul>');
          inList = false;
        }
        continue;
      }

      // Standard paragraph line
      if (inList) {
        result.push('</ul>');
        inList = false;
      }

      const pContent = this.escapeAndFormatInline(line);
      result.push(`<p class="desc-paragraph">${pContent}</p>`);
    }

    if (inList) {
      result.push('</ul>');
    }

    return result.join('\n');
  }

  private escapeAndFormatInline(str: string): string {
    let out = str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Bold formatting: **text**
    out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Inline code: `code`
    out = out.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    return out;
  }
}

