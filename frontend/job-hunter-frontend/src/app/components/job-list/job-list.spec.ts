import { ComponentFixture, TestBed } from '@angular/core/testing';
import { JobList } from './job-list';
import { JobModel } from '../../models/job.model';

describe('JobList', () => {
  let component: JobList;
  let fixture: ComponentFixture<JobList>;

  const createJob = (overrides: Partial<JobModel> = {}): JobModel => ({
    title: 'Senior Java Engineer',
    company: 'Fintech Corp',
    location: 'Remote',
    is_remote: true,
    clean_description: 'Building microservices',
    required_skills: ['Java', 'Spring Boot'],
    raw_payload: {},
    scraped_at: '2026-10-14T10:00:00Z',
    ...overrides,
  });

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [JobList],
    }).compileComponents();

    fixture = TestBed.createComponent(JobList);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should categorize APPLY / HIGH MATCH correctly', () => {
    const jobWithApply = createJob({ recommendation: 'APPLY' });
    expect(component['getRecommendationTier'](jobWithApply)).toBe('apply');
    expect(component['getRecommendationLabel'](jobWithApply)).toBe('APPLY');

    const jobWithHighMatch = createJob({ recommendation: 'HIGH MATCH' });
    expect(component['getRecommendationTier'](jobWithHighMatch)).toBe('apply');
    expect(component['getRecommendationLabel'](jobWithHighMatch)).toBe('HIGH MATCH');
  });

  it('should categorize CONSIDER correctly', () => {
    const jobWithConsider = createJob({ recommendation: 'CONSIDER' });
    expect(component['getRecommendationTier'](jobWithConsider)).toBe('consider');
    expect(component['getRecommendationLabel'](jobWithConsider)).toBe('CONSIDER');
  });

  it('should categorize SKIP correctly', () => {
    const jobWithSkip = createJob({ recommendation: 'SKIP' });
    expect(component['getRecommendationTier'](jobWithSkip)).toBe('skip');
    expect(component['getRecommendationLabel'](jobWithSkip)).toBe('SKIP');
  });

  it('should fallback to score when recommendation string is absent', () => {
    const highJob = createJob({ recommendation: null, score: 85 });
    expect(component['getRecommendationTier'](highJob)).toBe('apply');
    expect(component['getRecommendationLabel'](highJob)).toBe('HIGH MATCH');

    const midJob = createJob({ recommendation: null, score: 65 });
    expect(component['getRecommendationTier'](midJob)).toBe('consider');
    expect(component['getRecommendationLabel'](midJob)).toBe('CONSIDER');

    const lowJob = createJob({ recommendation: null, score: 40 });
    expect(component['getRecommendationTier'](lowJob)).toBe('skip');
    expect(component['getRecommendationLabel'](lowJob)).toBe('SKIP');
  });
});
