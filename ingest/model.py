"""Normalised records. Every parser returns one of these, whatever the vendor."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict

DRIFTED, PARSED, UNMATCHED = "DRIFTED", "PARSED", "UNMATCHED"


@dataclass
class Booking:
    channel: str                      # fareharbor | peek | airbnb | toast | square
    external_ref: str
    starts_at: Optional[str] = None
    trip: Optional[str] = None
    qty: int = 1
    total_cents: Optional[int] = None
    state: str = "confirmed"          # confirmed | cancelled
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None


@dataclass
class SalesSummary:
    channel: str
    business_day: str
    gross_cents: int
    orders: int
    items: Dict[str, int] = field(default_factory=dict)


@dataclass
class Result:
    status: str                       # PARSED | DRIFTED | UNMATCHED
    vendor: Optional[str] = None
    kind: Optional[str] = None        # booking | cancellation | sales_summary
    booking: Optional[Booking] = None
    summary: Optional[SalesSummary] = None
    missing: List[str] = field(default_factory=list)
    source_ref: Optional[str] = None

    @property
    def ok(self): return self.status == PARSED
