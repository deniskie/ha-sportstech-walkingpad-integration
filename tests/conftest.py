"""Shared test fixtures and stubs for sportstech_walkingpad tests.

Lightweight stubs for homeassistant.* and bleak* are injected before
the integration code is imported – no full HA instance required.
"""

from __future__ import annotations

import sys
import types


def _stub_module(name: str, **attrs: object) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


# ---------------------------------------------------------------------------
# homeassistant stubs
# ---------------------------------------------------------------------------

_stub_module("homeassistant")
_stub_module("homeassistant.core", HomeAssistant=object)
_stub_module("homeassistant.config_entries", ConfigEntry=object, config_entries=object)
_stub_module("homeassistant.const", Platform=object)
_stub_module("homeassistant.components")
_stub_module("homeassistant.components.bluetooth", async_discovered_service_info=lambda *a, **kw: [])
_stub_module(
    "homeassistant.components.bluetooth",
    async_discovered_service_info=lambda *a, **kw: [],
    BluetoothServiceInfoBleak=object,
)
_stub_module("homeassistant.data_entry_flow", FlowResult=dict)
_stub_module("homeassistant.helpers")
_stub_module("homeassistant.helpers.selector")
