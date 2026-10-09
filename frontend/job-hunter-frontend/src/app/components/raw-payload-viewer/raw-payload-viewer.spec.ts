import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RawPayloadViewer } from './raw-payload-viewer';

describe('RawPayloadViewer', () => {
  let component: RawPayloadViewer;
  let fixture: ComponentFixture<RawPayloadViewer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RawPayloadViewer],
    }).compileComponents();

    fixture = TestBed.createComponent(RawPayloadViewer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
