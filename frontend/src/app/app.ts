import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Api, User, Item, Category, Booking, Review, Page } from './api';

@Component({selector: 'app-root', imports: [CommonModule, FormsModule], templateUrl: './app.html', styleUrl: './app.css'})
export class App implements OnInit {
 private api = inject(Api);
 user: User | null = null;
 tab = 'browse'; items: Item[] = []; categories: Category[] = []; bookings: Booking[] = [];
 stats: Record<string, number> = {}; reviews: Review[] = [];
 search = ''; category = ''; loading = false; busy = false; error = ''; notice = ''; next: string | null = null;
 modal = ''; registerMode = false; selected: Item | null = null; reviewBooking: Booking | null = null;
 credentials = {username: '', email: '', password: ''};
 listing = {title: '', description: '', category: '', condition: 'good', location: ''};
 file: File | null = null;
 request = {start_date: '', end_date: '', message: ''};
 review = {rating: 5, comment: ''}; returnNotes = '';
 today = new Date().toLocaleDateString('en-CA');
 month = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
 ngOnInit() {
  this.api.get<Category[]>('categories/').subscribe({next: data => this.categories = data, error: e => this.fail(e)});
  if (sessionStorage.getItem('borrowhood-token')) {
   this.api.get<User>('auth/me/').subscribe({next: user => {this.user = user; this.refreshPrivate();}, error: () => sessionStorage.removeItem('borrowhood-token')});
  }
  this.loadItems();
 }
 fail(error: HttpErrorResponse) {
  this.busy = false; this.loading = false;
  if (error.status === 0) this.error = 'Cannot reach Borrowhood. Check that the backend is running.';
  else if (error.status === 401) { this.user = null; sessionStorage.removeItem('borrowhood-token'); this.error = 'Please sign in again.'; }
  else this.error = typeof error.error === 'object' ? Object.entries(error.error || {}).map(([key, value]) => `${key === 'detail' || key === 'non_field_errors' ? '' : key + ': '}${Array.isArray(value) ? value.join(' ') : value}`).join(' ') : 'Something went wrong. Please try again.';
 }
 switchTab(tab: string) {
  if (tab !== 'browse' && !this.user) { this.open('auth'); return; }
  this.tab = tab; this.error = ''; this.notice = '';
  if (tab === 'browse' || tab === 'mine') this.loadItems();
  else this.refreshPrivate();
 }
 loadItems(append = false) {
  this.loading = true; this.error = '';
  const query = new URLSearchParams({search: this.search, category: this.category});
  if (this.tab === 'mine') query.set('mine', '1');
  const path = append && this.next ? 'items/?' + new URL(this.next, location.origin).searchParams.toString() : 'items/?' + query;
  this.api.get<Page<Item>>(path).subscribe({next: data => {this.items = append ? [...this.items, ...data.results] : data.results; this.next = data.next; this.loading = false;}, error: e => this.fail(e)});
 }
 refreshPrivate() {
  if (!this.user) return;
  this.api.get<Record<string, number>>('dashboard/').subscribe({next: data => this.stats = data, error: e => this.fail(e)});
  this.bookings = [];
  this.loadBookings('bookings/');
 }
 private loadBookings(path: string) {
  this.api.get<Page<Booking>>(path).subscribe({next: data => {
   this.bookings = [...this.bookings, ...data.results];
   if (data.next) this.loadBookings('bookings/?' + new URL(data.next, location.origin).searchParams.toString());
  }, error: e => this.fail(e)});
 }
 open(modal: string, item: Item | null = null) {
  if (['listing', 'request'].includes(modal) && !this.user) modal = 'auth';
  this.error = ''; this.modal = modal; this.selected = item; this.file = null; this.reviews = [];
  this.listing = item ? {title: item.title, description: item.description, category: String(item.category), condition: item.condition, location: item.location} : {title: '', description: '', category: '', condition: 'good', location: ''};
  this.request = {start_date: this.today, end_date: this.today, message: ''};
  if (modal === 'request' && item) this.api.get<Page<Review>>(`reviews/?item=${item.id}`).subscribe({next: data => this.reviews = data.results, error: e => this.fail(e)});
 }
 close() { if (!this.busy) {this.modal = ''; this.error = '';} }
 authenticate() {
  this.busy = true; this.error = '';
  this.api.post<{token: string; user: User}>(`auth/${this.registerMode ? 'register' : 'login'}/`, this.credentials).subscribe({next: data => {
   sessionStorage.setItem('borrowhood-token', data.token); this.user = data.user; this.busy = false; this.modal = ''; this.credentials = {username: '', email: '', password: ''}; this.refreshPrivate(); this.notice = `Welcome, ${data.user.username}!`;
  }, error: e => this.fail(e)});
 }
 logout() {
  this.api.post('auth/me/', {}).subscribe({next: () => {sessionStorage.removeItem('borrowhood-token'); this.user = null; this.stats = {}; this.bookings = []; this.switchTab('browse');}, error: e => this.fail(e)});
 }
 onFile(event: Event) { this.file = (event.target as HTMLInputElement).files?.[0] ?? null; }
 saveItem() {
  this.busy = true; this.error = '';
  const data = new FormData(); Object.entries(this.listing).forEach(([key, value]) => data.append(key, value));
  if (this.file) data.append('image', this.file);
  const call = this.selected ? this.api.patch<Item>(`items/${this.selected.id}/`, data) : this.api.post<Item>('items/', data);
  call.subscribe({next: () => {this.busy = false; this.modal = ''; this.notice = 'Your listing is ready.'; this.loadItems(); this.refreshPrivate();}, error: e => this.fail(e)});
 }
 toggleItem(item: Item) {
  this.api.patch<Item>(`items/${item.id}/?mine=1`, {active: !item.active}).subscribe({next: () => {this.loadItems(); this.refreshPrivate();}, error: e => this.fail(e)});
 }
 requestItem() {
  if (!this.selected) return;
  this.busy = true; this.error = '';
  this.api.post('bookings/', {...this.request, item: this.selected.id}).subscribe({next: () => {this.busy = false; this.modal = ''; this.notice = 'Request sent! The owner will confirm your dates.'; this.refreshPrivate();}, error: e => this.fail(e)});
 }
 change(booking: Booking, action: string) {
  if (action === 'return') {this.reviewBooking = booking; this.returnNotes = ''; this.open('return'); return;}
  this.performTransition(booking, action);
 }
 performTransition(booking: Booking, action: string) {
  this.busy = true; this.error = '';
  this.api.post(`bookings/${booking.id}/transition/`, {action, return_notes: this.returnNotes}).subscribe({next: () => {this.busy = false; this.modal = ''; this.notice = 'Booking updated.'; this.refreshPrivate();}, error: e => this.fail(e)});
 }
 openReview(booking: Booking) {this.reviewBooking = booking; this.review = {rating: 5, comment: ''}; this.open('review');}
 saveReview() {
  this.busy = true;
  this.api.post('reviews/', {...this.review, booking: this.reviewBooking!.id}).subscribe({next: () => {this.busy = false; this.modal = ''; this.notice = 'Thanks for sharing your experience.'; this.refreshPrivate();}, error: e => this.fail(e)});
 }
 icon(category: string) { return ({Tools: '🛠️', Outdoors: '⛺', Photography: '📷', Games: '🎲'} as Record<string, string>)[category] || '📦'; }
 overdue(booking: Booking) { return booking.status === 'collected' && booking.end_date < this.today; }
 get monthLabel() { return this.month.toLocaleDateString('en-US', {month: 'long', year: 'numeric'}); }
 get days(): (number | null)[] {return [...Array(this.month.getDay()).fill(null), ...Array.from({length: new Date(this.month.getFullYear(), this.month.getMonth()+1, 0).getDate()}, (_, i) => i+1)];}
 moveMonth(delta: number) {this.month = new Date(this.month.getFullYear(), this.month.getMonth()+delta, 1);}
 dayBookings(day: number) {
  const date = `${this.month.getFullYear()}-${String(this.month.getMonth()+1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  return this.bookings.filter(b => ['approved', 'collected'].includes(b.status) && b.start_date <= date && b.end_date >= date);
 }
}
