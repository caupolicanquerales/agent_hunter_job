import { Injectable, inject } from "@angular/core";
import { HttpClient, HttpParams } from "@angular/common/http";
import { Observable } from "rxjs";

export type QueryParams = Record<string, string | number | boolean | null | undefined>;

@Injectable({
  providedIn: 'root'
})
export class SseGetService {

    private readonly http = inject(HttpClient);

    /**
     * Sends a GET request and emits the parsed JSON response.
     * Null and undefined params are omitted from the query string.
     */
    get<T = unknown>(url: string, params?: QueryParams): Observable<T> {
        let httpParams = new HttpParams();
        for (const [key, value] of Object.entries(params ?? {})) {
            if (value !== null && value !== undefined) {
                httpParams = httpParams.set(key, String(value));
            }
        }
        return this.http.get<T>(url, { params: httpParams });
    }


}