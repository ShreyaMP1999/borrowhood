import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpInterceptorFn } from '@angular/common/http';
export interface User { id: number; username: string }
export interface Category { id: number; name: string }
export interface Item { id: number; owner: number; owner_name: string; category: number; category_name: string; title: string; description: string; condition: string; location: string; image: string | null; active: boolean }
export interface Booking { id: number; item: number; item_title: string; owner: number; borrower: number; borrower_name: string; start_date: string; end_date: string; status: string; message: string; return_notes: string; reviewed: boolean }
export interface Review { id: number; author: string; rating: number; comment: string; item_title: string }
export interface Page<T> { results: T[]; next: string | null; count: number }
export const authInterceptor: HttpInterceptorFn = (request, next) => {
 const token = sessionStorage.getItem('borrowhood-token');
 return next(token && request.url.startsWith('/api/') ? request.clone({setHeaders: {Authorization: `Token ${token}`}}) : request);
};
@Injectable({providedIn: 'root'})
export class Api {
 private http = inject(HttpClient);
 get<T>(path: string) { return this.http.get<T>('/api/' + path); }
 post<T>(path: string, data: unknown) { return this.http.post<T>('/api/' + path, data); }
 patch<T>(path: string, data: unknown) { return this.http.patch<T>('/api/' + path, data); }
}
