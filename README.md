# FrontRow --- Backend

FrontRow is an event-booking application with a Python/FastAPI backend.
It provides account registration and login, venue and event management,
seat inventory and reservation workflows, and an AI-powered
event-discovery endpoint.

## Features

-   User registration and login
-   JWT-based authentication using cookies
-   Configurable access-token and refresh-token lifetimes
-   Venue creation with venue-seat inventory generated at creation time
-   Event creation with validation to prevent overlapping events at the
    same venue
-   Event-specific seat claims for held or booked seats
-   Configurable seat-hold duration
-   Structured-output LLM integration for event discovery
-   Event lookup based on supported criteria such as maximum price and
    capacity

Email verification is not currently implemented. Chat messages are not
persisted by the backend.

## Prerequisites

-   Python and pip
-   Docker and Docker Compose for the container-based setup
-   A configured `.env` file
-   Required database and LLM configuration values for the project

## Configure environment

From the backend project directory:

``` bash
cp .env.example .env
```

Populate `.env` with the values required by the application and its
dependencies.

Authentication settings described by the project include:

  Variable                      Purpose
  ----------------------------- -------------------------------------
  `JWT_ALGORITHM`               JWT signing algorithm
  `JWT_ACCESS_TOKEN_MINUTES`    Access-token lifetime in minutes
  `JWT_REFRESH_TOKEN_MINUTES`   Refresh-token lifetime in minutes
  `JWT_SECRET_KEY`              Secret used for JWT signing
  `RESERVE_HOLD_MIN`            Duration of a seat hold, in minutes

Do not commit secrets from `.env` to source control. Use strong,
environment-specific secrets outside local development.

## Install dependencies

If the repository contains `requirements.txt`, install its dependencies
with:

``` bash
pip install -r requirements.txt
```

Use the Python version specified by the project, if one is documented.

## Run locally

After configuring the environment and ensuring the required database and
other services are available:

``` bash
fastapi dev
```

If the application entry point is not auto-detected, provide the
appropriate module path for this repository, for example
`fastapi dev path/to/main.py`. Use the actual entry point from the
project.

## Run with Docker Compose

From the backend directory:

``` bash
docker compose up -d --build
```

This builds and starts the services defined in the Compose
configuration. Check the Compose file and service logs to confirm which
services are running and whether the API is already started inside a
container. If the API is running in Compose, you generally do not need
to start a second local `fastapi dev` process.

Useful commands:

``` bash
docker compose ps
docker compose logs -f
docker compose down
```

## Core design decisions

### Venue seats and event seat claims

When a venue is created, its `venue_seats` records are generated. This
avoids rebuilding the venue's seat inventory every time a seat map is
requested.

-   `venue_seats` is the canonical inventory of seats belonging to a
    venue.
-   `event_seat_claims` records event-specific seat claims, including
    reservation/hold state.
-   Joining the inventory with event-specific claims produces the seat
    list and status needed by the seat-map UI.

### Preventing overlapping events

Event creation obtains a PostgreSQL advisory transaction lock scoped to
the venue before checking for overlapping events. Requests for the same
venue contend on the same lock key. The later transaction waits for the
earlier one to commit or roll back, then performs its overlap check
against the resulting database state.

The transaction-scoped lock is released automatically at transaction
completion. This serializes the application-level check for a venue. A
database-level exclusion constraint on venue and time range could
provide an additional integrity safeguard; a plain `CHECK` constraint
cannot compare time ranges across separate rows.

### Preventing duplicate seat claims

Seat-hold and checkout operations use conditional database updates
rather than a separate read followed by an update. This reduces the
window in which concurrent requests can act on stale state.

A database uniqueness constraint prevents duplicate claims for the same
seat and event date. If concurrent transactions attempt conflicting
claims, the database rejects a conflicting write. The application should
handle that constraint violation and return a suitable conflict
response.

The precise guarantee depends on the conditional update predicates,
transaction boundaries, uniqueness key, and how expired holds and
checkout transitions are handled.

### Authentication

JWT configuration is supplied through environment variables. The access
token is short-lived. When it expires, the refresh flow can issue a new
access token and refresh token; if the refresh token is expired, the
user must log in again. Tokens are carried in cookies rather than
browser `localStorage`.

Passwords should be stored using a dedicated password-hashing algorithm
such as Argon2id, bcrypt, or scrypt. If the current implementation uses
HMAC alone for password storage, review that implementation before
production use; HMAC is not a standard password-storage scheme. Cookie
authentication should also be configured with appropriate `HttpOnly`,
`Secure`, and `SameSite` attributes and CSRF protection.

### AI event discovery

The backend sends the user's message to an LLM and requests structured
output. It then uses supported criteria---currently including maximum
price and capacity---to look up valid events and returns matching
results to the frontend. There is no backend conversation-memory
context, and chat messages are not stored by the backend. Seat-section
filtering is not implemented.

## Troubleshooting

-   **API fails to start:** Verify `.env`, the application entry point,
    and required services.
-   **Database connection fails:** Confirm database credentials,
    host/port, and that the database service is healthy.
-   **Concurrent seat request conflicts:** Ensure uniqueness violations
    are handled as expected application conflicts rather than unhandled
    server errors.
-   **Event overlap checks behave unexpectedly:** Confirm that the
    advisory-lock key is consistently derived from the venue ID and that
    lock acquisition, overlap query, and insert happen in the same
    transaction.
-   **LLM request fails:** Check the configured LLM credentials, network
    access, and structured-output schema.

## Security considerations

-   Keep secrets out of source control.
-   Use a dedicated password-hashing algorithm for stored passwords.
-   Configure JWT cookie attributes and CSRF protections for the
    deployment topology.
-   Handle uniqueness violations and expired holds deliberately.
-   Consider a database-level exclusion constraint for venue/time
    overlap if database-enforced protection is required.