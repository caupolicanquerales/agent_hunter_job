import { Injectable, inject } from "@angular/core";
import { Observable } from "rxjs";
import { QueryParams, SseGetService } from "./sse-get.service";

/** Query parameters accepted by the paginated /api/jobs/search endpoint. */
export interface JobSearchParams extends QueryParams {
    query: string;
    page?: number;
    page_size?: number;
    source?: string;
}

@Injectable({
    providedIn: 'root'
})
export class SseService {

    private readonly URL_ROOT: string = 'http://localhost:3100';
    private readonly URL_GET_JOBS: string = '/api/jobs/search';

    private readonly sseGetService = inject(SseGetService);

    getJobs<T = unknown>(searchParams: JobSearchParams): Observable<T> {
        return this.sseGetService.get<T>(`${this.URL_ROOT}${this.URL_GET_JOBS}`, searchParams);
    }

}