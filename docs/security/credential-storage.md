# OS-Backed Credential Vault Architecture & Secret Management

**Product:** AgentBreaker  
**Brand:** AshlynxCyber Security Systems  
**Audience:** Security Engineers, System Administrators, Cryptographic Auditors  
**Package:** `src/agentbreaker/core/credentials/`

---

## 1. Threat Landscape & Problem Statement

In AI security evaluation, testing targets frequently requires high-privilege credentials (production cloud LLM API keys, enterprise Gateway bearer tokens, or internal microservice passwords).

Storing credentials in plaintext files (e.g. `.env`, unencrypted JSON) on a developer or researcher workstation introduces severe supply-chain and exfiltration risks:
- Accidental Git commits or public repository pushes.
- Unauthorized read access by other local processes running under unprivileged user contexts.
- Workstation disk compromise or unencrypted backup leakage.

AgentBreaker resolves this by eliminating plaintext credential persistence entirely, delegating cryptographic operations directly to the host operating system's kernel and hardware-backed credential managers.

---

## 2. Platform Vault Implementations

AgentBreaker provides two platform-native credential store implementations:

```
                          ┌─────────────────────────────┐
                          │    CredentialStoreFactory   │
                          └──────────────┬──────────────┘
                                         │
                         Platform Check (sys.platform)
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
        sys.platform == "win32"                       sys.platform in ["linux", "darwin"]
                 │                                               │
                 ▼                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│   WindowsDPAPICredentialStore   │             │       POSIXCredentialStore      │
│  - CryptProtectData             │             │  - Linux: Secret Service (D-Bus)│
│  - CryptUnprotectData           │             │  - macOS: Keychain Services     │
│  - User Profile Master Key      │             │  - Fail-closed verification     │
└─────────────────────────────────┘             └─────────────────────────────────┘
```

---

### 2.1 Windows: Data Protection API (DPAPI)

On Windows (`win32`), AgentBreaker interfaces directly with `Crypt32.dll` via `ctypes`:
- **Encryption:** `CryptProtectData` binds the plaintext secret to the logged-on Windows user's Security Identifier (SID) and machine LSA/TPM master keys.
- **Decryption:** `CryptUnprotectData` decrypts the binary blob only when invoked by a process running within that exact user session.
- **Reference Scheme:** `vault://dpapi/target_<target_id>`
- **Storage Location:** `.credentials/<target_id>.vault` (contains encrypted binary DPAPI ciphertext).
- **Security Guarantees:**
  - Files cannot be decrypted by another user account on the same machine (returns `SEC_E_DECRYPT_FAILURE`).
  - Files copied to another physical machine cannot be decrypted.

---

### 2.2 POSIX: Linux Secret Service & macOS Keychain

On Linux and macOS (`darwin`), AgentBreaker utilizes authentic OS keyrings via the `keyring` library (`keyring>=25.7.0`):
- **macOS:** Binds directly to the native Apple Keychain (`keyring.backends.macOS.Keyring`).
- **Linux:** Binds to the Freedesktop Secret Service standard over D-Bus (`SecretServiceKeyring`), interfacing with GNOME Keyring or KWallet.
- **Reference Scheme:** `vault://keyring/target_<target_id>`
- **Fail-Closed Guarantee:**
  - In headless or containerized environments lacking an active Secret Service session, `keyring` resolves to `fail.Keyring` or a backend with non-positive priority.
  - When this occurs, `POSIXCredentialStore` raises `SecureStorageUnavailableError`.
  - **Insecure Fallback Prohibition:** The system **never falls back to plaintext or weak XOR obfuscation**.

---

## 3. Legacy Migration Service (`CredentialMigrator`)

When AgentBreaker discovers legacy target definitions with plaintext `api_key` attributes or legacy XOR-based vault references (`vault://posix/`), `CredentialMigrator` automatically upgrades them:

1. **Detection:** Inspects `.agentbreaker/targets/*.json` for raw strings or legacy references.
2. **Migration:** Decrypts legacy values and commits them into the active OS vault.
3. **Atomic Target Update:** Rewrites the target configuration file with the new `vault://` reference using an atomic file swap (`.tmp` write followed by `os.replace`).
4. **Idempotency:** Targets already referencing the modern OS vault format are skipped without modification.
5. **Zero-Log Guarantee:** The migration process logs target IDs and vault references only; raw secret values are zeroed in memory and never logged.

---

## 4. Headless Server & Container Setup (Linux)

In headless Linux servers, CI/CD workers, or Docker containers without a graphical desktop session, a D-Bus Secret Service session must be initialized before using the OS vault:

```bash
# Ubuntu / Debian headless setup
sudo apt-get install -y dbus gnome-keyring python3-keyring

# Launch with D-Bus session
dbus-run-session -- agentbreaker target add my-target ...
```
If a headless environment cannot provide a Secret Service session, targets should use environment variable references (`target_id` configured with an empty secret, and credentials provided via runtime environment variables).

