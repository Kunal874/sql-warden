"""Validated execution limits for the early safe slice."""

from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class QueryLimits:
    """Finite server-owned budgets; bad configuration must fail before a query."""

    max_rows: int = 1000
    max_result_bytes: int = 2 * 1024 * 1024
    max_cell_bytes: int = 64 * 1024
    statement_timeout_ms: int = 5000
    lock_timeout_ms: int = 500
    pool_timeout_ms: int = 5000
    total_timeout_ms: int = 15000
    max_estimated_cost: int = 100000
    max_estimated_rows: int = 100000

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{field.name} must be a positive integer")
        if self.max_cell_bytes > self.max_result_bytes:
            raise ValueError("max_cell_bytes cannot exceed max_result_bytes")
        if self.lock_timeout_ms > self.statement_timeout_ms:
            raise ValueError("lock_timeout_ms cannot exceed statement_timeout_ms")
        for name in ("statement_timeout_ms", "pool_timeout_ms"):
            if getattr(self, name) > self.total_timeout_ms:
                raise ValueError(f"{name} cannot exceed total_timeout_ms")
