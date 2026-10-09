import { Injectable, computed, signal } from '@angular/core';
import { JobFilterCriteria, JobModel, JobSortOption } from '../models/job.model';

const INITIAL_JOBS: JobModel[] = [
  {
    id: 'f87a31b2-9d32-48a1-b841-39659b918101',
    external_job_id: 'twikey-sr-java-dev-918',
    source_portal: 'WeWorkRemotely',
    title: 'Senior Java Backend Engineer',
    company: 'Twikey',
    location: 'Ghent, Belgium',
    is_remote: true,
    salary_min: 85000,
    salary_max: 110000,
    currency: 'EUR',
    match_score: 0.96,
    scraped_at: '2026-10-08T10:15:00Z',
    required_skills: ['Java', 'Spring Boot', 'PostgreSQL', 'Microservices', 'Fintech', 'Distributed Systems', 'Docker'],
    clean_description: `Twikey is seeking a Senior Java Backend Engineer to drive the evolution of our high-volume European payment orchestration platform.

### Core Responsibilities
- Architect, implement, and maintain mission-critical backend microservices handling recurring payments and SEPA mandates.
- Optimize database transactions, concurrency, and caching across distributed PostgreSQL clusters with pgvector indexing.
- Collaborate with frontend engineers, product managers, and security officers to enforce PCI-DSS compliance and zero-trust principles.
- Conduct thorough peer code reviews and mentor junior developers in clean architecture, unit testing, and Domain-Driven Design (DDD).

### Key Requirements
- 6+ years of professional experience building scalable backend services with Java (17/21) and the Spring ecosystem (Spring Boot, Spring Data, Spring Security).
- Deep expertise in relational databases (PostgreSQL), complex query optimization, and transaction isolation levels.
- Demonstrated experience designing resilient RESTful APIs and asynchronous event-driven workflows with RabbitMQ or Apache Kafka.
- Strong grounding in containerization (Docker, Kubernetes) and CI/CD pipelines (GitLab CI, GitHub Actions).
- Excellent English communication skills; comfortable in a remote-first international engineering team.`,
    raw_payload: {
      status_code: 200,
      url: 'https://weworkremotely.com/remote-jobs/twikey-senior-java-developer',
      parser_version: 'v2.4.1',
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'x-crawler-node': 'eu-central-1-collector-04'
      },
      scraper_meta: {
        extractor: 'wwr_html_article_extractor',
        raw_category: 'Dev / Backend Programming',
        tags: ['fintech', 'java', 'backend', 'payments'],
        html_length_bytes: 48920,
        cleaned_chars: 1480
      },
      attributes: {
        apply_url: 'https://www.twikey.com/jobs/sr-java-engineer',
        workplace_type: 'Fully Remote',
        applicant_tracking_system: 'lever',
        published_timestamp: 1728382500
      }
    }
  },
  {
    id: 'a12bc94e-28f1-460b-8d9e-1144a8b29f02',
    external_job_id: 'proxify-node-nest-441',
    source_portal: 'Proxify Network',
    title: 'Senior Backend Developer (Node.js / Nest.js)',
    company: 'Proxify AB',
    location: 'Stockholm, Sweden',
    is_remote: true,
    salary_min: 75000,
    salary_max: 95000,
    currency: 'USD',
    match_score: 0.93,
    scraped_at: '2026-10-08T08:30:00Z',
    required_skills: ['Node.js', 'Nest.js', 'TypeScript', 'PostgreSQL', 'Docker', 'GraphQL', 'AWS'],
    clean_description: `Proxify is searching for an experienced Senior Backend Developer specializing in TypeScript and Nest.js to construct robust enterprise APIs.

### What you will do
- Design, build, and deploy production-grade REST and GraphQL endpoints for top-tier European tech startups.
- Leverage TypeScript strict mode, Nest.js dependency injection, and Prisma/TypeORM for clean domain separation.
- Implement comprehensive automated test suites including unit, integration, and load testing with Jest and k6.
- Partner with product designers and frontend teams to optimize API payloads and response latency.

### Candidate Profile
- 5+ years of software engineering experience with Node.js and at least 3 years focused on Nest.js.
- Strong command of TypeScript, design patterns, microservices architectures, and OpenAPI specifications.
- Practical knowledge of PostgreSQL, Redis caching, and message queues (RabbitMQ or Redis Streams).
- Located in CET timezone (±3 hours) with seamless conversational and written English proficiency.`,
    raw_payload: {
      status_code: 200,
      url: 'https://weworkremotely.com/remote-jobs/proxify-ab-senior-backend-developer-node-js-nest-js-3',
      parser_version: 'v2.4.1',
      headers: {
        'content-type': 'application/json',
        'server': 'cloudflare'
      },
      scraper_meta: {
        extractor: 'generic_json_ld_extractor',
        raw_category: 'Full-Stack / Backend',
        tags: ['typescript', 'nestjs', 'nodejs', 'aws'],
        html_length_bytes: 36240,
        cleaned_chars: 1190
      },
      attributes: {
        hiring_org_lei: '549300XYZ99PROXIFY',
        telecommute_status: '100% Remote',
        timezone_requirement: 'CET +/- 3 hours'
      }
    }
  },
  {
    id: 'c74de901-447a-4ec9-8921-2e921d743a03',
    external_job_id: 'reddit-backend-iam-552',
    source_portal: 'Greenhouse/Reddit',
    title: 'Staff Backend Engineer, IAM & Security',
    company: 'Reddit',
    location: 'San Francisco, CA',
    is_remote: true,
    salary_min: 175000,
    salary_max: 230000,
    currency: 'USD',
    match_score: 0.90,
    scraped_at: '2026-10-07T14:20:00Z',
    required_skills: ['Distributed Systems', 'Go', 'IAM', 'OAuth2', 'Kubernetes', 'PostgreSQL', 'Architecture'],
    clean_description: `Reddit's Identity & Access Management (IAM) team creates and maintains hyper-scale authorization systems safeguarding over 100M daily active users.

### The Role & Impact
- Architect next-generation authentication and federated identity protocols serving billions of monthly transactions.
- Harden backend infrastructure against credential stuffing, automated bots, and account takeover vectors.
- Define internal IAM standards, token lifecycle management, and fine-grained access control (ABAC/RBAC) frameworks.
- Collaborate with the Site Reliability Engineering and Core Infrastructure teams on multi-region failover strategies.

### What We Are Looking For
- Extensive track record operating large-scale distributed systems in production with Go, Rust, or Java.
- Deep comprehension of modern authentication specs: OAuth 2.0, OpenID Connect, WebAuthn/Passkeys, and SAML.
- Strong knowledge of high-throughput data stores (Cassandra, PostgreSQL, Redis) and low-latency gRPC services.
- Experience with zero-trust networking and Kubernetes service mesh architectures.`,
    raw_payload: {
      status_code: 200,
      url: 'https://boards.greenhouse.io/reddit/jobs/6092144',
      parser_version: 'v2.4.1',
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'x-request-id': 'req-rdt-77189a'
      },
      scraper_meta: {
        extractor: 'greenhouse_api_crawler',
        raw_category: 'Infrastructure & Security',
        tags: ['security', 'iam', 'golang', 'distributed-systems'],
        html_length_bytes: 52180,
        cleaned_chars: 1430
      },
      attributes: {
        department: 'Security Engineering',
        security_clearance_required: false,
        equity_offered: true
      }
    }
  },
  {
    id: 'e3948cb1-871d-4054-941e-62738a192304',
    external_job_id: 'stripe-infra-reliability-108',
    source_portal: 'Stripe Careers',
    title: 'Staff Infrastructure Engineer - Data Platform',
    company: 'Stripe',
    location: 'Seattle, WA',
    is_remote: true,
    salary_min: 195000,
    salary_max: 260000,
    currency: 'USD',
    match_score: 0.88,
    scraped_at: '2026-10-06T18:00:00Z',
    required_skills: ['Architecture', 'PostgreSQL', 'Go', 'Distributed Systems', 'Kafka', 'Kubernetes'],
    clean_description: `Stripe is looking for a Staff Engineer to join our Core Data Platform group to design fault-tolerant data storage engines.

### Mission
- Ensure five-nines (99.999%) availability across core ledger persistence layers processing billions in economic volume.
- Build automated schema management, replication verification, and cross-region consensus mechanisms.
- Drive database modernization initiatives around pgvector, columnar query engines, and distributed locks.

### Requirements
- Demonstrated background guiding architectural decisions across distributed engineering teams.
- Deep understanding of database internals, WAL replication, MVCC, and storage tiering.
- Proficiency in Go or Java with production troubleshooting acumen under high traffic conditions.`,
    raw_payload: {
      status_code: 200,
      url: 'https://stripe.com/jobs/listings/staff-infra-data',
      parser_version: 'v2.4.1',
      headers: {
        'content-type': 'application/json',
        'x-stripe-region': 'us-west-2'
      },
      scraper_meta: {
        extractor: 'custom_headless_crawler',
        tags: ['infrastructure', 'postgres', 'fintech', 'reliability'],
        html_length_bytes: 61040,
        cleaned_chars: 1100
      },
      attributes: {
        job_board_source: 'direct_crawl',
        remote_allowed_countries: ['US', 'CA', 'UK']
      }
    }
  },
  {
    id: 'b45c991e-3991-4df0-9302-841801c44805',
    external_job_id: 'dremio-query-eng-201',
    source_portal: 'Dremio Careers',
    title: 'Software Engineer - Query Execution Engine',
    company: 'Dremio',
    location: 'Santa Clara, CA',
    is_remote: false,
    salary_min: 145000,
    salary_max: 185000,
    currency: 'USD',
    match_score: 0.82,
    scraped_at: '2026-10-05T11:45:00Z',
    required_skills: ['Java', 'C++', 'Architecture', 'Query Engine', 'Distributed Systems', 'Apache Arrow'],
    clean_description: `Dremio delivers a unified data lakehouse engine powered by Apache Iceberg and Apache Arrow.

### Position Overview
- Develop runtime components responsible for executing analytical SQL queries at petabyte scale.
- Implement, optimize, and benchmark vectorized query operators, expression evaluators, and memory managers.
- Minimize CPU cache misses and enhance parallel execution pipelines across heterogeneous clusters.

### Qualifications
- B.S., M.S., or Ph.D. in Computer Science or equivalent software engineering experience.
- Strong software development capabilities in Java or modern C++ (C++17/20).
- Solid comprehension of operating systems, CPU memory hierarchies, and concurrent algorithms.`,
    raw_payload: {
      status_code: 200,
      url: 'https://www.dremio.com/careers/software-engineer-query-execution',
      parser_version: 'v2.4.1',
      headers: {
        'content-type': 'application/json',
        'x-cdn': 'fastly'
      },
      scraper_meta: {
        extractor: 'lever_api_crawler',
        tags: ['systems', 'c++', 'java', 'arrow', 'database-internals'],
        html_length_bytes: 38200,
        cleaned_chars: 980
      },
      attributes: {
        on_site_schedule: 'Hybrid / Santa Clara HQ',
        requires_visa_sponsorship: false
      }
    }
  },
  {
    id: 'd92a104c-12b4-4b5f-a342-990145214006',
    external_job_id: 'abnormal-dir-sec-902',
    source_portal: 'Abnormal AI Portal',
    title: 'Director of Security Engineering',
    company: 'Abnormal AI',
    location: 'New York, NY',
    is_remote: true,
    salary_min: 220000,
    salary_max: 280000,
    currency: 'USD',
    match_score: 0.79,
    scraped_at: '2026-10-04T16:10:00Z',
    required_skills: ['Architecture', 'Leadership', 'Cloud', 'Python', 'FedRAMP', 'Security'],
    clean_description: `Abnormal AI protects modern enterprises against sophisticated social engineering and AI-driven cyber attacks.

### Leadership Scope
- Build and scale high-performing security engineering teams across Cloud, AppSec, and Infrastructure domains.
- Oversee FedRAMP High and DoD IL5 authorization readiness and commercial zero-trust architectures.
- Partner with executive leadership to establish security as a core competitive differentiator.

### Background
- Deep technical foundation in software engineering with successful progression into engineering management.
- Hands-on experience securing multi-tenant AWS environments and machine learning inference pipelines.`,
    raw_payload: {
      status_code: 200,
      url: 'https://abnormal.ai/careers/director-security',
      parser_version: 'v2.4.1',
      headers: {
        'content-type': 'application/json'
      },
      scraper_meta: {
        extractor: 'greenhouse_crawler',
        tags: ['security', 'leadership', 'fedramp', 'ai'],
        html_length_bytes: 42100,
        cleaned_chars: 890
      },
      attributes: {
        department: 'Security Leadership',
        reports_to: 'CISO'
      }
    }
  }
];

@Injectable({
  providedIn: 'root'
})
export class JobService {
  private readonly _jobs = signal<JobModel[]>(INITIAL_JOBS);
  private readonly _selectedJobId = signal<string | null>(INITIAL_JOBS[0]?.id ?? null);
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

