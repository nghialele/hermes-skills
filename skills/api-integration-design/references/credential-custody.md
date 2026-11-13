# Credential custody for a hosted multi-tenant tool

Applies when one deployment holds many customers' API keys. Say the blast radius out loud in
the design; hiding it does not reduce it.

## Envelope encryption

- Master key (KEK) from env or a secret manager. It never touches the database.
- Per-link random 256-bit data key (DEK), encrypted under the KEK, stored beside the
  ciphertext.
- AES-256-GCM with AAD binding `identity_id + purpose + version`, so a ciphertext cannot be
  moved between rows or tables.
- Rotation rewraps DEKs; it does not rewrite data.

## Linking flow

1. Command in a **DM**, never a public channel — channel history is forever and often
   searchable.
2. One-time URL on your own domain. Explain exactly which scopes to tick, with the vendor's
   settings path.
3. The user pastes the key into the page, not into chat or a chat modal.
4. Prove the key works before storing it: one cheap authenticated read plus the vendor's
   scopes endpoint. Show the user what the bot will be able to do with *their* key.
5. On confirm: encrypt, burn the linking token, DM a summary. Revocation deletes the
   ciphertext and writes an audit row.

If a key is ever pasted into a channel: delete the message, tell the user to rotate, refuse to
use it. Do not "rescue" the paste.

## Never stored, never displayed

- panel passwords, 2FA codes, revealed env values, database passwords
- the key itself in logs, errors, audit rows, model context, or crash reports

Displayed instead: last 4 characters, key fingerprint, scopes, linking date. That is enough
for a user to identify which key is which and decide to rotate.

## Audit

Store a redacted argument snapshot: hashes and lengths for anything marked `secret`. The
audit row answers "what did this identity do, when, and did it succeed" — never "what was the
value".

## Blast radius, stated plainly

If the database and the KEK are both compromised, every customer key is compromised. The only
honest mitigations are: read-only default scopes, a one-command revocation instruction, a
written incident path, and keeping the KEK in a KMS rather than a file on the same host.

## Second credential, separate custody

A bring-your-own LLM credential is a different secret with a different lifecycle from the
vendor API key. Separate table, separate encryption purpose, separate revocation. Never let
one unlock the other.
