import asyncio
import logging
import types

import pytest

from nds_crawler_svc.app import startup_event, app


def dummy_cleanup():
    dummy_cleanup.called = True

dummy_cleanup.called = False


@pytest.fixture(autouse=True)
def override_cleanup(monkeypatch):
    # Override the cleanup_old_data function in the app module with dummy_cleanup
    monkeypatch.setattr("nds_crawler_svc.app.cleanup_old_data", dummy_cleanup)
    yield
    # Cleanup: reset the flag
    dummy_cleanup.called = False


def test_startup_event_schedules_cleanup():
    # Run the asynchronous startup_event
    asyncio.run(startup_event())
    # Check that dummy_cleanup was called during startup_event (immediate cleanup invocation)
    assert dummy_cleanup.called, "cleanup_old_data was not invoked during startup_event"
    # Verify that the scheduler is attached to the app state
    assert hasattr(app.state, "scheduler"), "Scheduler not attached to app.state"
    # Shutdown scheduler after test to clean up
    app.state.scheduler.shutdown()
