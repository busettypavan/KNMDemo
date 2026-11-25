"""Account settings (sign-in, lockout, cookie and reset lifetimes), read from the environment (and .env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AccountSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cookie_secure: bool = True  # COOKIE_SECURE: false only for plain-http local development
    token_ttl_seconds: int = 3600  # TOKEN_TTL_SECONDS: session lifetime (cookie Max-Age and token exp)
    login_max_failures: int = 5  # LOGIN_MAX_FAILURES: failed sign-ins before a lock
    login_lock_seconds: int = 900  # LOGIN_LOCK_SECONDS: how long a lock lasts
    reset_ttl_seconds: int = 900  # RESET_TTL_SECONDS: password reset link lifetime
