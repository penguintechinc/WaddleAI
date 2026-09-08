"""Regression tests: every license-server call carries an explicit timeout.

`PenguinTechLicenseClient.__init__` used to do `self.session.timeout = timeout`.
`requests.Session` accepts the attribute but `Session.request()` never reads it
(verified against requests 2.34.2), so the setting bought nothing and every call
to license.penguintech.io was unbounded — a hung or blackholed license server
could block the caller indefinitely on a path that is supposed to degrade
gracefully. These tests pin the per-request `timeout=` kwarg, the only form
requests honours.
"""

from unittest.mock import MagicMock, patch

import pytest

from shared.licensing.python_client import PenguinTechLicenseClient

_TIMEOUT = 7


@pytest.fixture
def client() -> PenguinTechLicenseClient:
    """A license client with a distinctive timeout, so a default can't masquerade as a pass."""
    return PenguinTechLicenseClient(license_key="lic-test", product="waddleai", timeout=_TIMEOUT)


def _ok_response(payload: dict) -> MagicMock:
    """A 200-ish response stub whose json() returns `payload`."""
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def test_validate_passes_timeout(client: PenguinTechLicenseClient) -> None:
    """validate() sends timeout= on its POST."""
    with patch.object(client.session, "post") as post:
        post.return_value = _ok_response({"valid": True, "features": []})
        client.validate()

    assert post.call_args.kwargs["timeout"] == _TIMEOUT


def test_check_feature_passes_timeout(client: PenguinTechLicenseClient) -> None:
    """The feature-entitlement POST sends timeout=."""
    with patch.object(client.session, "post") as post:
        post.return_value = _ok_response({"features": [{"name": "waddleai", "entitled": True}]})
        assert client.check_feature("waddleai", use_cache=False) is True

    assert post.call_args.kwargs["timeout"] == _TIMEOUT


def test_keepalive_passes_timeout(client: PenguinTechLicenseClient) -> None:
    """The keepalive POST sends timeout=.

    server_id is pre-set so keepalive() does not first route through validate()
    -- that would leave the assertion reading validate()'s call, not this one.
    """
    client.server_id = "srv-1"
    with patch.object(client.session, "post") as post:
        post.return_value = _ok_response({"status": "ok"})
        client.keepalive()

    assert post.call_count == 1
    assert post.call_args.args[0].endswith("/api/v2/keepalive")
    assert post.call_args.kwargs["timeout"] == _TIMEOUT


def test_session_timeout_attribute_is_not_relied_on(client: PenguinTechLicenseClient) -> None:
    """The Session must not carry a `timeout` attribute standing in for the real thing.

    Guards the exact regression: setting it looks like configuring a timeout,
    reads as configured in review, and does nothing at runtime.
    """
    assert not hasattr(client.session, "timeout")
