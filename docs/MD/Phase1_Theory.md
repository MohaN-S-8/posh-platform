# Phase 1 Theory Guide — What You Need to Learn

**Read this alongside building. Every concept here maps directly to code you already wrote or are about to write.**

---

## TOPIC 1: How the Web Works (Request → Response Cycle)

Before writing any backend code, you must understand what happens when a browser makes a request.

```
Browser                    FastAPI Backend              MySQL Database
  │                              │                            │
  │──── POST /api/v1/auth/login ─►│                            │
  │     (sends email + password)  │                            │
  │                              │──── SELECT * FROM users ──►│
  │                              │◄─── returns user row ───────│
  │                              │                            │
  │◄─── 200 OK + JWT token ───────│                            │
```

**Key concepts:**
- **HTTP Methods**: GET (read), POST (create), PUT (update full), PATCH (update partial), DELETE
- **Status Codes**: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Validation Error, 500 Server Error
- **Request**: has URL, method, headers, body (JSON)
- **Response**: has status code, headers, body (JSON)
- **REST API**: a standard way to design URLs and use HTTP methods consistently

**Where you used this:** Every endpoint in `app/api/v1/auth.py`

---

## TOPIC 2: FastAPI — How It Works

FastAPI is a Python framework that makes building APIs fast and easy.

### How a request flows through FastAPI:

```
HTTP Request
     │
     ▼
  Middleware (CORS check, rate limit)
     │
     ▼
  Router (which function handles this URL?)
     │
     ▼
  Dependency Injection (get_db, get_current_user)
     │
     ▼
  Pydantic Validation (is the request body valid?)
     │
     ▼
  Your function (signup, login, etc.)
     │
     ▼
  Service Layer (business logic)
     │
     ▼
  Repository / DB Layer (SQL queries)
     │
     ▼
  HTTP Response (JSON)
```

### Key FastAPI concepts:

**1. Path operations (routes)**
```python
@router.post("/signup")         # POST method, /signup URL
async def signup(data: SignupRequest, db = Depends(get_db)):
    pass
```

**2. Dependency Injection — `Depends()`**
```python
# get_db is called automatically before your function runs
# It gives you a database session, then cleans up after
async def signup(db: AsyncSession = Depends(get_db)):
    pass
```
Think of `Depends()` as "before running my function, run this other function first and give me its result."

**3. Pydantic models (schemas)**
```python
class SignupRequest(BaseModel):
    email: EmailStr    # FastAPI validates this automatically
    password: str
```
If the request body doesn't match this shape, FastAPI returns 422 automatically — you don't write any validation code for that.

**4. Async/Await**
```python
async def signup(...):          # this function can pause while waiting
    result = await db.execute() # pause here, let other requests run
```
`async` means the function can be paused while waiting for slow things (DB queries, network). This lets FastAPI handle many requests at once efficiently.

---

## TOPIC 3: Pydantic — Data Validation

Pydantic is the library that validates data in FastAPI. Every `SignupRequest`, `LoginRequest` etc. is a Pydantic model.

**How it works:**
```python
from pydantic import BaseModel, field_validator

class SignupRequest(BaseModel):
    first_name: str          # type annotation = basic validation
    email: EmailStr          # special type = email format check

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v):
        v = v.strip()        # v = the actual value sent by user
        if len(v) < 2:
            raise ValueError("Too short")  # this becomes a 422 response
        return v             # always return the (possibly modified) value
```

**Why two layers of validation?**
- Frontend (React + Zod): gives instant feedback to user
- Backend (Pydantic): the real gate — protects the API from direct attacks
- **Never trust only client-side validation**

---

## TOPIC 4: SQLAlchemy — ORM (Object Relational Mapper)

An ORM lets you write Python code instead of raw SQL. SQLAlchemy translates your Python into SQL automatically.

**Without ORM (dangerous — SQL injection risk):**
```python
query = f"SELECT * FROM users WHERE email = '{email}'"  # NEVER DO THIS
```

**With SQLAlchemy ORM (safe):**
```python
result = await db.execute(
    select(UserMaster).where(UserMaster.email == email)
)
# SQLAlchemy generates parameterized SQL: SELECT * FROM users WHERE email = ?
# Parameters are passed separately — SQL injection is impossible
```

### Models vs Schemas — the most confusing part for beginners:

| | SQLAlchemy Model | Pydantic Schema |
|---|---|---|
| File location | `app/models/` | `app/schemas/` |
| Purpose | Represents a DB table | Represents API request/response |
| Example | `UserMaster` | `SignupRequest`, `TokenResponse` |
| Used for | DB queries | Input validation + output shape |

**A request's journey:**
```
JSON body (from browser)
    → Pydantic Schema validates it (SignupRequest)
    → Service creates SQLAlchemy Model instance (UserMaster)
    → SQLAlchemy saves it to MySQL
    → Pydantic Schema formats the response (TokenResponse)
    → JSON body (to browser)
```

### Async SQLAlchemy — why we use it:
```python
# Sync (blocks the server while waiting for DB):
result = db.execute(query)      # server frozen during this

# Async (server handles other requests while waiting):
result = await db.execute(query)  # server free during this
```

---

## TOPIC 5: Alembic — Database Migrations

Alembic tracks database schema changes like Git tracks code changes.

**Why you need it:**
- Without migrations: every developer has a different DB schema
- With migrations: everyone runs `alembic upgrade head` and gets the same schema

**How it works:**
```
You change a model (add a column)
    ↓
alembic revision --autogenerate -m "add column"
    ↓
Alembic compares current DB schema vs your models
    ↓
Generates a migration file with upgrade() and downgrade()
    ↓
alembic upgrade head → applies the change to DB
```

**The migration file:**
```python
def upgrade() -> None:
    op.add_column('user_master',
        sa.Column('phone_verified', sa.Boolean(), default=False)
    )

def downgrade() -> None:
    op.drop_column('user_master', 'phone_verified')
    # downgrade lets you undo the migration if something goes wrong
```

**Rule:** Never hand-edit the database. Always go through Alembic.

---

## TOPIC 6: Authentication — JWT (JSON Web Tokens)

JWT is the industry standard for stateless authentication in APIs.

### Why not sessions?
- Traditional sessions: server stores "user X is logged in" in memory
- Problem: if you have 3 servers, which one has the session?
- JWT: the token itself contains the user info — server stores nothing

### How JWT works:

```
Login
  User sends email + password
      ↓
  Server verifies password
      ↓
  Server creates JWT token:
      Header.Payload.Signature
      │         │         │
      │         │         └── proves token wasn't tampered with
      │         └── contains: user_id, role_id, company_id, expiry
      └── algorithm used
      ↓
  Server sends token to client
      ↓
  Client stores token (in httpOnly cookie — not localStorage)

Every subsequent request
  Client sends token in cookie automatically
      ↓
  Server decodes token (no DB lookup needed)
      ↓
  Server knows who the user is
```

### Access token vs Refresh token:

| | Access Token | Refresh Token |
|---|---|---|
| Expiry | 15 minutes | 7 days |
| Stored in | httpOnly cookie | httpOnly cookie |
| Stored in DB | No | Yes (hashed) |
| Used for | Every API request | Getting new access token |
| If stolen | Usable for 15 min max | Can be revoked in DB |

### Why httpOnly cookies (not localStorage)?
- localStorage: JavaScript can read it → XSS attack can steal your token
- httpOnly cookie: JavaScript CANNOT read it → XSS attack fails
- This is the single most important auth security decision

---

## TOPIC 7: Password Security

**Never store plaintext passwords. Ever.**

### bcrypt hashing:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# When user signs up:
hashed = pwd_context.hash("MyPassword@123")
# Stores something like: $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW

# When user logs in:
is_valid = pwd_context.verify("MyPassword@123", hashed)
# Returns True or False
```

**Why bcrypt?**
- It's intentionally slow (takes ~100ms to hash)
- Even if your DB is stolen, attacker can't reverse the hash
- Has a "salt" built in — two identical passwords produce different hashes
- Cost factor (12 in our config) = how slow it is = how hard to brute force

### OTP (One-Time Password) flow:
```
Signup
  → Generate 6-digit random number (raw OTP)
  → Hash it with SHA-256
  → Store HASH in DB (never store raw OTP)
  → Send raw OTP to user's email
  → User submits OTP
  → Hash what they submitted → compare to stored hash
  → If match → verify → delete/expire OTP
```

**Why hash the OTP?** If your DB is breached, attacker can't use stored OTPs.

---

## TOPIC 8: Account Security — Brute Force Protection

A brute force attack = trying millions of passwords until one works.

**Our protection (from Login Screen doc — requirement #28):**
```
Attempt 1-4: return "Invalid credentials" (don't reveal which is wrong)
Attempt 5:   return "Account locked for 15 minutes"
After 15min: automatically unlock, reset counter
Successful login: reset counter immediately
```

**Why "Invalid email or password" (not "email not found")?**
- If you say "email not found", attacker knows valid emails
- Always return the same message regardless of which failed
- This is called "user enumeration prevention"

**Two-layer rate limiting:**
- Per-user lockout (`account_lockout` table) — we built this
- Per-IP rate limiting (`slowapi` middleware) — protects against distributed attacks

---

## TOPIC 9: Layered Architecture — Why We Split Into Routers/Services/Repositories

Our backend has 3 layers:

```
app/api/v1/auth.py        ← Router layer
    │                        Handles HTTP (request/response format)
    │                        No business logic here
    ▼
app/services/auth_service.py  ← Service layer
    │                            Business logic lives here
    │                            Validation, rules, workflows
    ▼
app/repositories/             ← Repository layer (we'll add this)
                               Raw DB queries
                               No business logic here
```

**Why does this matter?**

```python
# BAD — logic mixed into router (hard to test, hard to change)
@router.post("/login")
async def login(data, db):
    user = await db.execute(select(UserMaster)...)
    if not user:
        raise HTTPException(401)
    if not verify_password(data.password, user.password_hash):
        # increment lockout...
        raise HTTPException(401)
    # ...20 more lines of logic

# GOOD — router just calls service (easy to test, easy to change)
@router.post("/login")
async def login(data, request, db):
    return await auth_service.login(db, data, request.client.host)
```

**Testing benefit:** You can test `AuthService.login()` without HTTP at all. You can also test the router by mocking `AuthService.login()` (which is exactly what we did in `test_auth.py`).

---

## TOPIC 10: Multi-Tenancy — company_id Scoping

This platform serves multiple companies (tenants) sharing one database.

**The rule:** Every query for company data must filter by `company_id` from the JWT token — never from the request body.

**Why this is critical:**
```python
# DANGEROUS — trusts company_id from request:
@router.get("/employees")
async def get_employees(company_id: int, db, user=Depends(get_current_user)):
    return await db.execute(
        select(UserMaster).where(UserMaster.company_id == company_id)
        # Attacker sends company_id=2 and sees another company's employees!
    )

# SAFE — uses company_id from JWT token:
@router.get("/employees")
async def get_employees(db, user=Depends(get_current_user)):
    return await db.execute(
        select(UserMaster).where(UserMaster.company_id == user.company_id)
        # company_id comes from the verified JWT — can't be tampered with
    )
```

**Where company_id comes from:**
1. User logs in → JWT created with their `company_id`
2. Every request sends this JWT
3. Backend extracts `company_id` from JWT (not from request params)
4. All queries filter by this `company_id`

---

## TOPIC 11: RBAC — Role-Based Access Control

Different users can do different things based on their role.

**Our roles (from `role_master`):**
```
Super Admin  → can do everything across all companies
Company Admin → can manage their company's data
HR           → can upload employees, assign training, view reports
Employee     → can only watch videos, take assessments, download certificates
```

**How RBAC works in FastAPI:**
```python
# 1. At login: permissions are loaded and put into JWT
access_token = create_access_token({
    "user_id": 1,
    "role_id": 3,           # HR
    "permissions": ["Employee_Upload", "Training_Assign", "Reports_View"]
})

# 2. On each request: check permission before running the function
def require_permission(permission_name: str):
    def checker(current_user = Depends(get_current_user)):
        if permission_name not in current_user.permissions:
            raise HTTPException(403, "Forbidden")
        return current_user
    return checker

# 3. Applied to routes:
@router.post("/videos", dependencies=[Depends(require_permission("Training_Assign"))])
async def upload_video(...):
    pass  # only runs if user has Training_Assign permission
```

---

## TOPIC 12: Testing Strategy — Unit vs Integration

**Unit tests** (what we wrote):
- Test one thing in isolation
- Mock (fake) everything external (DB, email, etc.)
- Run in milliseconds
- Don't need Docker running

**Integration tests** (coming in later phases):
- Test multiple components together
- Use a real test database
- Slower but catch more real bugs

**The key principle we learned:**
```python
# Wrong: mock at the DB level (unreliable with FastAPI's Depends)
with patch("app.api.v1.auth.get_db") as mock:
    ...

# Right: mock at the service level (reliable, fast, correct)
with patch("app.services.auth_service.AuthService.login") as mock:
    ...

# Right: override dependency for DB-level tests
app.dependency_overrides[get_db] = lambda: fake_db_session
```

**Test naming convention:**
```python
def test_signup_empty_first_name():   # test_{function}_{scenario}
def test_login_invalid_credentials():
def test_video_cannot_fast_forward():
```

---

## TOPIC 13: Git — Version Control Workflow

**What you've been doing:**
```bash
# Make changes to code
git add .                    # stage changes (tell git "track these")
git commit -m "feat: ..."    # save a snapshot with a message
git push origin develop       # send to GitHub
```

**Commit message convention (Conventional Commits):**
```
feat(auth): add OTP verification     → new feature
fix(login): handle locked accounts   → bug fix
chore(deps): update fastapi          → maintenance
docs(readme): add setup steps        → documentation
test(auth): add signup validation tests → tests
refactor(service): split auth logic  → code improvement (no behaviour change)
```

**Why this matters:**
- Clear history of what changed and why
- Auto-generates changelogs
- Makes code review easier
- Future-you will thank present-you

---

## Summary — What Phase 1 Teaches You

| Concept | Where you used it |
|---|---|
| HTTP request/response cycle | Every endpoint |
| FastAPI routing + Depends | `app/api/v1/auth.py` |
| Pydantic validation | `app/schemas/auth.py` |
| SQLAlchemy ORM (async) | `app/services/auth_service.py` |
| Alembic migrations | `alembic/versions/` |
| bcrypt password hashing | `app/core/security.py` |
| JWT access + refresh tokens | `app/core/security.py` |
| OTP generation + hashing | `app/core/security.py` |
| Account lockout / brute force | `app/services/auth_service.py` |
| Layered architecture | routers → services → DB |
| Multi-tenancy (company_id) | `auth_service.py` signup |
| Unit testing + mocking | `tests/test_auth.py` |
| Git + conventional commits | Every commit |

**You are now past the hardest conceptual phase.** Everything that follows (videos, certificates, HR portal) uses the same patterns — just different business logic on top of the same foundation.
