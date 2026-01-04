# Passkey Implementation Plan (Issue #145)

## Overview
Implement WebAuthn passkey support as the primary authentication method, with password-based auth as an optional fallback and secure account recovery mechanisms.

## Goals
1. **Primary**: Passkey authentication using WebAuthn API
2. **Fallback**: Optional password authentication
3. **Recovery**: Secure account recovery for lost passkeys
4. **UX**: Seamless, user-friendly authentication flow

---

## Architecture

### Frontend Components

#### 1. PasskeyRegistration Component
- **Location**: `frontend/src/components/PasskeyRegistration.jsx`
- **Purpose**: Handle passkey creation during user onboarding
- **Flow**:
  1. User clicks "Create Passkey"
  2. Call backend `/api/auth/passkey/register/begin`
  3. Get challenge and user info
  4. Call `navigator.credentials.create()` with WebAuthn options
  5. Send credential to `/api/auth/passkey/register/complete`
  6. Store credential ID for future auth

#### 2. PasskeyLogin Component
- **Location**: `frontend/src/components/PasskeyLogin.jsx`
- **Purpose**: Handle passkey authentication
- **Flow**:
  1. User clicks "Sign in with Passkey"
  2. Call backend `/api/auth/passkey/login/begin`
  3. Get challenge
  4. Call `navigator.credentials.get()` with WebAuthn options
  5. Send assertion to `/api/auth/passkey/login/complete`
  6. Receive JWT token and user data

#### 3. Updated Login Page
- **Location**: `frontend/src/pages/Login.jsx`
- **Changes**:
  - Passkey button as primary auth method
  - "Use password instead" link (opt-in)
  - Graceful fallback for unsupported browsers

#### 4. Account Recovery Flow
- **Location**: `frontend/src/pages/AccountRecovery.jsx`
- **Options**:
  - **Option A**: Admin-assisted recovery (send request to admin)
  - **Option B**: Recovery codes (generate 8 single-use codes during setup)
  - **Option C**: Secondary email verification

---

### Backend Implementation

#### 1. New Database Tables

```sql
-- Passkey credentials table
CREATE TABLE passkey_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    credential_id TEXT NOT NULL UNIQUE,  -- Base64url encoded
    public_key TEXT NOT NULL,             -- Stored public key
    counter INTEGER DEFAULT 0,            -- Signature counter for replay protection
    transports TEXT,                      -- JSON array of transports (usb, nfc, ble, internal)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    device_name TEXT,                     -- Optional user-friendly name
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Recovery codes table
CREATE TABLE recovery_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    code_hash TEXT NOT NULL,  -- Hashed recovery code
    used BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Passkey challenges (temporary storage)
CREATE TABLE passkey_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,           -- NULL for login challenges
    username TEXT,             -- For login flow
    challenge TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. New API Endpoints

##### Authentication Routes (`backend/routes/auth.py`)

```python
# Passkey Registration
POST /api/auth/passkey/register/begin
  - Input: { username }
  - Output: { challenge, user, excludeCredentials }
  - Creates challenge and returns WebAuthn registration options

POST /api/auth/passkey/register/complete
  - Input: { credential, username, challengeId }
  - Output: { success, credentialId }
  - Verifies and stores the new credential

# Passkey Login
POST /api/auth/passkey/login/begin
  - Input: { username? }  # Optional for discoverable credentials
  - Output: { challenge, allowCredentials }
  - Creates challenge and returns WebAuthn authentication options

POST /api/auth/passkey/login/complete
  - Input: { assertion, challengeId }
  - Output: { token, user }
  - Verifies assertion and returns JWT token

# Recovery
POST /api/auth/recovery/generate-codes
  - Requires JWT
  - Output: { codes: string[] }
  - Generates 8 recovery codes (show once, user must save)

POST /api/auth/recovery/use-code
  - Input: { username, recoveryCode }
  - Output: { temporaryToken }
  - Allows user to create new passkey

GET /api/auth/passkeys
  - Requires JWT
  - Output: { passkeys: [{ id, deviceName, createdAt, lastUsedAt }] }
  - List user's registered passkeys

DELETE /api/auth/passkeys/:id
  - Requires JWT
  - Removes a specific passkey (must have at least one remaining)
```

#### 3. Python Dependencies

```python
# requirements.txt additions
webauthn>=1.11.0  # py_webauthn library for WebAuthn server
cryptography>=41.0.0  # For key operations (may already be installed)
```

#### 4. WebAuthn Configuration

```python
# backend/config.py or backend/utils/webauthn_config.py

RP_ID = "thefreezer.xyz"  # Relying Party ID (your domain)
RP_NAME = "Freezer Inventory Tracker"
ORIGIN_DEV = "https://dev.thefreezer.xyz"
ORIGIN_PROD = "https://thefreezer.xyz"

# Challenge timeout
CHALLENGE_TIMEOUT_SECONDS = 300  # 5 minutes
```

---

## Implementation Phases

### Phase 1: Backend Foundation (Days 1-2)
1. ✅ Install webauthn library
2. ✅ Create database migration for new tables
3. ✅ Implement registration begin/complete endpoints
4. ✅ Implement login begin/complete endpoints
5. ✅ Add challenge cleanup cron job

### Phase 2: Frontend Integration (Days 3-4)
1. ✅ Create PasskeyRegistration component
2. ✅ Create PasskeyLogin component
3. ✅ Update Login page with passkey primary option
4. ✅ Add browser compatibility checks
5. ✅ Handle errors gracefully (unsupported browser, user cancellation)

### Phase 3: Recovery System (Day 5)
1. ✅ Generate recovery codes on passkey creation
2. ✅ Create recovery code redemption flow
3. ✅ Allow users to view/manage their passkeys in Settings
4. ✅ Implement "remove passkey" with safety checks

### Phase 4: Password Fallback (Day 6)
1. ✅ Add "Use password instead" option on login page
2. ✅ Update user registration to optionally set password
3. ✅ Allow users to add/remove password in Settings
4. ✅ Password reset flow (email-based or admin-assisted)

### Phase 5: Testing & Polish (Day 7)
1. ✅ Test on multiple devices (iOS, Android, desktop)
2. ✅ Test on multiple browsers (Chrome, Safari, Firefox, Edge)
3. ✅ Security review (challenge replay, credential validation)
4. ✅ UX polish (loading states, error messages, help text)
5. ✅ Documentation for users

---

## Security Considerations

### 1. Challenge Management
- ✅ Challenges expire after 5 minutes
- ✅ Challenges are single-use (delete after verification)
- ✅ Use cryptographically random challenges (32 bytes)

### 2. Credential Storage
- ✅ Never store private keys (only public keys)
- ✅ Validate credential ID uniqueness
- ✅ Check signature counter to detect cloned authenticators

### 3. Recovery Codes
- ✅ Hash recovery codes before storage (bcrypt)
- ✅ Codes are single-use
- ✅ Minimum 128-bit entropy (20 characters)
- ✅ Warn user to save codes securely

### 4. Account Lockout
- ✅ Prevent removal of last authentication method
- ✅ Require current authentication to remove passkey
- ✅ Admin override for account recovery

---

## User Experience Flow

### First-Time User Registration
1. User enters username
2. System prompts: "Secure your account with a passkey"
3. User clicks "Create Passkey"
4. Browser shows platform authenticator (Face ID, Windows Hello, etc.)
5. User authenticates
6. System shows recovery codes: "Save these codes - you'll need them if you lose access"
7. User confirms they've saved codes
8. Registration complete

### Returning User Login
1. User lands on login page
2. System shows: "Sign in with your passkey" (big button)
3. Below: "Use password instead" (small link)
4. User clicks passkey button
5. Browser shows authenticator prompt
6. User authenticates → logged in

### Lost Passkey Recovery
1. User clicks "I lost my passkey"
2. System prompts for username
3. User enters recovery code
4. System allows user to register new passkey
5. Recovery code is marked as used

---

## Browser Compatibility

### Supported
- ✅ Chrome/Edge 67+ (Windows, macOS, Android)
- ✅ Safari 16+ (iOS, macOS)
- ✅ Firefox 122+ (Windows, macOS, Android)

### Fallback
- ❌ Older browsers → show "Use password instead"
- ❌ Check `PublicKeyCredential` in window object

---

## Testing Checklist

### Device Matrix
- [ ] iOS Safari (iPhone/iPad)
- [ ] Android Chrome
- [ ] macOS Safari (TouchID)
- [ ] macOS Chrome (TouchID)
- [ ] Windows Chrome (Windows Hello)
- [ ] Windows Edge (Windows Hello)
- [ ] Linux Chrome (USB security key)

### Scenarios
- [ ] New user registration with passkey
- [ ] Login with passkey
- [ ] Login with password fallback
- [ ] Recovery code generation
- [ ] Recovery code redemption
- [ ] Multiple passkeys per user
- [ ] Remove passkey (with 1+ remaining)
- [ ] Prevent removal of last auth method
- [ ] Challenge expiration
- [ ] Invalid challenge rejection
- [ ] Cloned authenticator detection (counter check)

---

## Migration Strategy

### For Existing Users
1. **Opt-in period**: Existing users keep password auth
2. **Prompt to add passkey**: Show banner in app encouraging passkey setup
3. **Dual auth**: Allow both passkey + password during transition
4. **Eventually**: Encourage passkey-only (but don't force)

### For New Users
1. **Passkey-first**: Registration flow defaults to passkey
2. **Optional password**: "Advanced: Add password backup" link
3. **Recovery codes**: Always generate for passkey users

---

## Open Questions / Decisions Needed

1. **Recovery method preference?**
   - ☑ Recovery codes (recommended)
   - ☐ Admin-assisted recovery
   - ☐ Email verification

2. **Enforce passkey-only for new users?**
   - ☐ Yes - more secure
   - ☑ No - let users choose (better adoption)

3. **Allow username-less login?**
   - ☑ Yes - support discoverable credentials (better UX)
   - ☐ No - require username first

4. **Passkey naming**
   - ☑ Auto-detect device name (e.g., "iPhone 14 Pro")
   - ☑ Allow user to customize name

---

## Dependencies & Libraries

### Frontend
```json
{
  "@simplewebauthn/browser": "^9.0.0"
}
```

### Backend
```python
webauthn==1.11.1
```

---

## Rollout Plan

1. **Week 1**: Backend implementation + database migration
2. **Week 2**: Frontend components + integration
3. **Week 3**: Testing on multiple devices/browsers
4. **Week 4**: Beta testing with select users
5. **Week 5**: Production rollout with monitoring

---

## Success Metrics

- [ ] 80%+ of new users create passkey
- [ ] <5% use password fallback
- [ ] Zero account lockouts due to lost passkeys (recovery works)
- [ ] <1% login failures
- [ ] Page load time impact <100ms

---

## References

- [WebAuthn Spec](https://www.w3.org/TR/webauthn-3/)
- [SimpleWebAuthn Library](https://simplewebauthn.dev/)
- [py_webauthn Docs](https://github.com/duo-labs/py_webauthn)
- [WebAuthn Guide (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API)
