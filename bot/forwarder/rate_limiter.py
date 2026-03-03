import asyncio
import time


class TokenBucketRateLimiter:
    def __init__(self, rate: float = 25, burst: int = 0):
        self.rate = rate
        self.burst = burst if burst else int(rate)
        self.tokens = float(self.burst)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_refill = now

    async def acquire(self):
        while True:
            async with self._lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate
            await asyncio.sleep(wait)
