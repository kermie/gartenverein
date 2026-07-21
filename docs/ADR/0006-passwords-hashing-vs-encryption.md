# Passwords: hashing vs. encryption

Two different needs, two different tools:

- **Login passwords** (app users): **bcrypt** (hash, one-way). The app
  never needs to recover the original, only compare against it.
- **SMTP password** (for sending mail): **Fernet/AES** (encryption,
  reversible) in `app/crypto_utils.py`. The app actually has to log in to
  the mail server with it, so a hash would be useless here.

The encryption key is derived from `SECRET_KEY` via SHA-256 (not to hash a
password, but to produce a 32-byte key in the form Fernet requires). If
`SECRET_KEY` changes, already-encrypted values become unreadable --
`SECRET_KEY` should therefore stay stable and secret.

