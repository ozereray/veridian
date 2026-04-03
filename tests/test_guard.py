import pytest
from veridian.guard import guard

def test_guard_success():
    @guard(max_retries=3)
    def always_works():
        return "ok"
    assert always_works() == "ok"

def test_guard_retry_then_succeed():
    attempts = {"count": 0}

    @guard(max_retries=3, delay=0)
    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("not yet")
        return "done"

    assert flaky() == "done"
    assert attempts["count"] == 3

def test_guard_exhausted_raises():
    @guard(max_retries=2, delay=0)
    def always_fails():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        always_fails()

def test_guard_fallback():
    @guard(max_retries=2, delay=0, fallback="default")
    def always_fails():
        raise ValueError("err")

    assert always_fails() == "default"