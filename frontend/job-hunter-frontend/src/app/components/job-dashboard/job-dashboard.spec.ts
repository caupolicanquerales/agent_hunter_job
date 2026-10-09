import { ComponentFixture, TestBed } from '@angular/core/testing';
import { JobDashboard } from './job-dashboard';

describe('JobDashboard', () => {
  let component: JobDashboard;
  let fixture: ComponentFixture<JobDashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [JobDashboard],
    }).compileComponents();

    fixture = TestBed.createComponent(JobDashboard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
