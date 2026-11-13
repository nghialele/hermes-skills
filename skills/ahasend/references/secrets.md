# Credential handling for the AhaSend CLI

## The facts (verified against v0.5.0 source and a live run)

- Credentials live in `~/.ahasend/config.yaml` (`%USERPROFILE%\.ahasend\config.yaml`), **plaintext YAML**, `profiles.<name>.api_key`.
- `internal/config/config.go` sets the dir to `0700` and the file to `0600` via `os.Chmod`. **On Windows that is a no-op for ACLs**: the created `%USERPROFILE%\.ahasend` keeps inherited ACEs, so `SYSTEM`, `BUILTIN\Administrators` and the owning user all hold Full control. On Linux/macOS the modes are real.
- There is **no** environment-variable support: `grep -rn os.Getenv` over the source finds only `TERM`, `NO_COLOR` and `HOME`. The docs state this as a design decision.
- There is no `--api-key-stdin` or file flag. The only credential-shaped input on stdin is `smtp send --password-stdin`.
- A single choke point resolves credentials: `internal/auth/auth.go` → `defaultAuthenticatedClientResolver`. Flags first, then the profile.

## Patched build on this machine (preferred)

`C:\Users\Administrator\bin\ahasend.exe` — **v0.5.0-keyring**, commit `4e6a611`. Source: `C:\Users\Administrator\src\ahasend-cli`, branch `feat/credentials-from-environment-and-keyring`. Patch: `C:\Users\Administrator\src\ahasend-cli-keyring-credentials.patch`. Upstream PR text: `C:\Users\Administrator\src\PR-ahasend-credentials.md`.

It adds two credential sources, resolved in this order:

| Order | Source |
| --- | --- |
| 1 | `--api-key` + `--account-id` (always the production API) |
| 2 | `AHASEND_API_KEY` + `AHASEND_ACCOUNT_ID` (+ optional `AHASEND_API_URL`), when no `--profile` is given |
| 3 | OS credential store entry named by `--profile`, else `default` |
| 4 | `~/.ahasend/config.yaml` profile (stock behaviour) |

### Keychain storage — the recommended setup here

```powershell
C:\Users\Administrator\bin\ahasend.exe auth login --keyring        # prompts, verifies, stores in Credential Manager
C:\Users\Administrator\bin\ahasend.exe auth logout --keyring       # remove the entry
```

- Entry name is the profile name; `cmdkey /list` shows `LegacyGeneric:target=ahasend:default`.
- Holds key + account ID + API URL as JSON in one secret; nothing is written to `config.yaml`.
- An entry **wins over** a profile of the same name in the file. Remove it with `auth logout --keyring` to go back to the file's profile.
- `auth status` reads the file only; use `ahasend ping --profile <name>` to verify an entry.
- A store that cannot be read (headless Linux, no Secret Service) silently falls back to the file.

### Environment — for containers, CI, one-off shells

```bash
AHASEND_API_KEY=... AHASEND_ACCOUNT_ID=<uuid> ahasend domains list
```

`export` them from a secret store; never pass the key as `--api-key` on a command line. An unusable value exits 4 and names the variable rather than falling back to a profile.

## Stock CLI on this machine (npm `@ahasend/cli` v0.5.0)

Use only if the patched binary is unavailable. Two options, best first.

### 1. DPAPI blob + wrapper (installed at `%USERPROFILE%\.ahasend-secret\`)

`%USERPROFILE%\.ahasend-secret\` holds:

- `store.ps1` — prompts for the key (`Read-Host -AsSecureString`, input hidden, never in argv), validates the account UUID, writes `creds.clixml` encrypted with **DPAPI** (decryptable only by this Windows user on this machine), then sets an owner-only ACL on the folder.
- `ah.ps1` / `ah` — decrypt into process memory and exec `ahasend --api-key … --account-id … "$@"`. Refuses `auth status|switch|logout` (they reject `--api-key`) and exits 3 when no blob exists.

```bash
powershell -File "$USERPROFILE/.ahasend-secret/store.ps1"   # run yourself, once
./ah ping
./ah domains list --output json
```

Residual exposure: the decrypted key lands in the `ahasend` child's `argv`, visible to processes running **as the same user**. Strictly better than a plaintext file readable by SYSTEM/Administrators, strictly worse than option 1.

### 2. Plaintext profile, hardened

If the operator prefers `ahasend auth login`:

```bash
icacls "%USERPROFILE%\.ahasend" /inheritance:r /grant:r "%USERNAME%:(OI)(CI)F" "SYSTEM:(OI)(CI)F"
icacls "%USERPROFILE%\.ahasend\config.yaml" /inheritance:r /grant:r "%USERNAME%:(F)"
```

Then reduce blast radius, which matters more than storage format:

- One profile per environment (`--profile production` / `staging` / `sandbox`).
- Send-only keys scoped to `messages:send:{domain}` + `statistics:read:{domain}`; a separate management key for domains/webhooks/campaigns.
- **IP allow list** on every key (`apikeys create --ip-allow-list <cidr>`) so a leaked key is useless off your infrastructure.
- Sandbox-mode keys for anything that is not production.
- Rotate: `apikeys create` prints the secret once; `apikeys delete <old>` after the switch.
- Never `cat` the config, never paste the key in chat, never commit it.

## Rules for the agent

- Never ask for, accept, echo or store an API key or SMTP password in chat or in a file. The operator runs `auth login --keyring` (patched) or `store.ps1` (stock) themselves.
- Prefer the patched binary with a keychain entry: it keeps the key out of both `argv` and plaintext files. Fall back to `ah <cmd>` only when the patched binary is missing.
- `ah auth status` always fails (exit 4) by design — use `ping` to verify credentials.
- When reporting an auth failure, distinguish exit 2 (key rejected / absent) from 6 (scope or IP allow list) and 8 (rate limit).
