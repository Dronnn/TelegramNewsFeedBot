import time

import pytest

from bot.forwarder.rate_limiter import TokenBucketRateLimiter


@pytest.mark.asyncio
async def test_acquire_without_wait():
    """First N requests up to burst should pass immediately."""
    limiter = TokenBucketRateLimiter(rate=25, burst=5)

    start = time.monotonic()
    for _ in range(5):
        await limiter.acquire()
    elapsed = time.monotonic() - start

    assert elapsed < 0.05, f"Expected near-instant, took {elapsed:.3f}s"


@pytest.mark.asyncio
async def test_acquire_with_wait():
    """After exhausting burst, next acquire should wait."""
    limiter = TokenBucketRateLimiter(rate=10, burst=1)

    start = time.monotonic()
    await limiter.acquire()  # instant — uses the single burst token
    first = time.monotonic() - start

    await limiter.acquire()  # must wait for a token refill
    second = time.monotonic() - start

    assert first < 0.05, f"First acquire should be instant, took {first:.3f}s"
    assert second >= 0.08, f"Second acquire should wait ~0.1s, took {second:.3f}s"


@pytest.mark.asyncio
async def test_rate_over_time():
    """Over 1 second, approximately 'rate' requests should go through."""
    rate = 10
    limiter = TokenBucketRateLimiter(rate=rate, burst=1)

    count = 0
    start = time.monotonic()
    while time.monotonic() - start < 1.0:
        await limiter.acquire()
        count += 1

    # First acquire is instant (burst token), then ~rate per second after that.
    # Allow a tolerance band of +/- 3.
    assert abs(count - rate) <= 3, (
        f"Expected ~{rate} acquires in 1s, got {count}"
    )
