# Borrowhood API

Base path: `/api/`. JSON requests except photos, which use `multipart/form-data`.
Authenticated requests send `Authorization: Token <token>`. In the browser, tokens are stored in sessionStorage and revoked on sign-out.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | auth/register/ | Create account: username, email, password |
| POST | auth/login/ | Sign in: username, password |
| GET | auth/me/ | Current user ID and username |
| POST | auth/me/ | Revoke token and sign out |
| GET | categories/ | Category array |
| GET | items/ | Paginated active listings |
| POST | items/ | Create listing |
| GET | items/{id}/ | Listing detail |
| PATCH | items/{id}/ | Owner edits listing |
| GET | items/?mine=1 | Current user's active and paused listings |
| PATCH | items/{id}/?mine=1 | Edit or resume a paused listing |
| GET | bookings/ | Paginated bookings where you are owner or borrower |
| GET | bookings/{id}/ | Participant-only detail |
| POST | bookings/ | Create pending request |
| POST | bookings/{id}/transition/ | Change status through an authorized action |
| GET | reviews/?item={id} | Public reviews for an item |
| POST | reviews/ | Review your returned booking once |
| GET | dashboard/ | Your lending and borrowing counts |

Item filters: `search` (title, description, neighborhood), `category` (ID), `mine=1`, and `page`. Paginated responses contain `count`, `next`, `previous`, and `results` with 24 records per page; categories are unpaginated.

## Create a listing

Fields: `title` (120 characters), `description`, `category` (ID), `condition` (`new`, `good`, `fair`), `location` (120 characters), optional `image` (validated image under 5 MB), optional `active` (boolean). Owner is always the authenticated user. PATCH supports the same fields. Pause instead of deleting so booking history is retained.

## Borrow an item

```json
{
  "item": 1,
  "start_date": "2030-05-12",
  "end_date": "2030-05-14",
  "message": "Working on a weekend shelf project!"
}
```

Use today or a future date. End dates are inclusive: May 12–14 conflicts with another booking starting May 14. Requests do not reserve inventory until approved.

## Booking actions

```json
{"action": "approve"}
```

| Action | Actor | From | To |
| --- | --- | --- | --- |
| approve | Owner | pending | approved |
| decline | Owner | pending | declined |
| collect | Owner | approved | collected |
| return | Owner | collected | returned |
| cancel | Borrower | pending, approved | cancelled |

`return` accepts optional `return_notes` (up to 1000 characters). Pickup cannot be confirmed before the start date. Approvals require an active listing, a non-expired start date, and no overlap with an approved or collected booking. A return clears the reservation. Reviews accept `booking`, `rating` (1–5), and optional `comment` (1000 characters).

Errors use HTTP 400 for invalid input/state, 401 for missing or expired credentials, 403 for forbidden actions, 404 for inaccessible records, and 429 for throttling. Error bodies contain a `detail`, field errors, or a list of messages. Anonymous access is limited to 120 requests/hour; anonymous login and registration share a 20/hour limit. These use Django's default local-memory cache; distributed production throttling requires a shared cache.
