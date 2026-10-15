# The 10 build segments

The Git history records the project in these ten ordered commits:

1. **Project setup** — Django scaffold, dependencies, environment configuration and ignored local files.
2. **SQL data model** — categories, items, bookings, reviews, foreign keys, indexes and migrations.
3. **Accounts** — registration, password validation, token login, profile and logout.
4. **Item listings** — listing creation/editing, photo uploads, search, filters and owner permissions.
5. **Borrowing workflow** — requests, approvals, cancellation, collection, returns and transactional conflict protection.
6. **Community insights** — verified reviews, private dashboard metrics and repeatable demo data.
7. **Angular foundation** — frontend scaffold, typed HTTP client, authentication interceptor and development proxy.
8. **User experience** — responsive explore page, item forms, requests, loan management and reservation calendar.
9. **Verification** — 24 API/concurrency tests, production build checks, readable formatting and GitHub Actions.
10. **Delivery** — Docker Compose, API/architecture documentation, SQL examples, screenshots and setup guide.

Each segment is a real change to the repository. Later commits build on earlier segments; the final commit is the complete runnable MVP.
