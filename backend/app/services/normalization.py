from decimal import Decimal, InvalidOperation

CATEGORY_MAP = {
    "subscription": "subscription",
    "plan": "subscription",
    "monthly plan": "subscription",
    "annual plan": "subscription",
    "seat": "seat",
    "seat license": "seat",
    "per seat": "seat",
    "user seat": "seat",
    "api": "api",
    "api usage": "api",
    "usage": "api",
    "tokens": "api",
    "credit": "credit",
    "credit purchase": "credit",
    "prepaid credit": "credit",
    "adjustment": "adjustment",
    "refund": "adjustment",
    "promo": "adjustment",
}

BASIS_MAP = {
    "invoice": "invoiced",
    "invoiced": "invoiced",
    "bill": "invoiced",
    "usage": "usage",
    "consumption": "usage",
    "payment": "payment",
    "cash": "payment",
    "credit": "credit",
    "prepaid": "credit",
}

KNOWN_PROVIDERS = {"openai", "anthropic"}


def normalize_expense_category(raw: str | None) -> str:
    if not raw:
        return "api"
    key = raw.strip().lower()
    return CATEGORY_MAP.get(key, "api")


def normalize_financial_basis(raw: str | None) -> str:
    if not raw:
        return "invoiced"
    key = raw.strip().lower()
    return BASIS_MAP.get(key, "invoiced")


def normalize_provider(raw: str | None) -> str:
    if not raw:
        return "unknown"
    cleaned = raw.strip().lower()
    if "openai" in cleaned or "chatgpt" in cleaned:
        return "openai"
    if "anthropic" in cleaned or "claude" in cleaned:
        return "anthropic"
    return cleaned


def normalize_currency(raw: str | None, default: str = "USD") -> str:
    if not raw:
        return default
    return raw.strip().upper()[:3]


def normalize_amount(raw: str | int | float | Decimal | None) -> Decimal:
    """Parse an amount to Decimal. Raises ValueError if unparseable or negative where not expected."""
    if raw is None:
        raise ValueError("Amount is required")
    if isinstance(raw, Decimal):
        return raw
    try:
        return Decimal(str(raw))
    except InvalidOperation as exc:
        raise ValueError(f"Cannot parse amount: {raw!r}") from exc
