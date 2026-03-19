# system_reboot_required - CheckMK agent-based check plugin
#
# Copyright (C) 2026  Luca-Leon Hausdoerfer - (cmk@hausdoerfer.dev)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import time
from typing import Any

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    Result,
    Service,
    State,
    StringTable,
)

Section = dict[str, Any]

_DEFAULT_PARAMS: dict[str, Any] = {
    "warn_hours": 12,
    "crit_hours": 24,
}


def parse_system_reboot_required(string_table: StringTable) -> Section:
    parsed: Section = {}
    for line in string_table:
        if len(line) < 2:
            continue
        key = line[0].rstrip(":")
        value = " ".join(line[1:]).strip()
        parsed[key] = value
    return parsed


def discover_system_reboot_required(section: Section):
    if section:
        yield Service()


def check_system_reboot_required(params: dict[str, Any], section: Section):
    if not section:
        yield Result(state=State.UNKNOWN, summary="No data received from agent plugin")
        return

    reboot_required = section.get("reboot_required", "0")
    detection_method = section.get("detection_method", "unknown")
    since_timestamp = section.get("since_timestamp", "unknown")
    packages = section.get("packages", "unknown")

    if reboot_required != "1":
        yield Result(state=State.OK, summary="No reboot pending")
        return

    # Build summary parts
    summary_parts = [f"Reboot pending (detected via: {detection_method})"]

    # Determine age and state
    if since_timestamp == "unknown":
        # Cannot determine age → immediate CRIT
        state = State.CRIT
        summary_parts.append("pending since: unknown")
    else:
        try:
            ts = float(since_timestamp)
            age_seconds = time.time() - ts
            age_hours = age_seconds / 3600.0

            warn_hours = params.get("warn_hours", _DEFAULT_PARAMS["warn_hours"])
            crit_hours = params.get("crit_hours", _DEFAULT_PARAMS["crit_hours"])

            hours_int = int(age_hours)
            minutes_int = int((age_hours - hours_int) * 60)
            if hours_int > 0:
                age_str = f"{hours_int}h {minutes_int}m"
            else:
                age_str = f"{minutes_int}m"

            summary_parts.append(f"pending since: {age_str}")

            if age_hours >= crit_hours:
                state = State.CRIT
            elif age_hours >= warn_hours:
                state = State.WARN
            else:
                state = State.OK  # reboot required but still within acceptable window
        except ValueError:
            state = State.CRIT
            summary_parts.append("pending since: unknown (invalid timestamp)")

    if packages and packages not in ("unknown", "none"):
        pkg_list = packages.split(",")
        if len(pkg_list) > 5:
            summary_parts.append(f"packages: {', '.join(pkg_list[:5])} (+{len(pkg_list) - 5} more)")
        else:
            summary_parts.append(f"packages: {packages}")

    yield Result(state=state, summary=", ".join(summary_parts))


agent_section_system_reboot_required = AgentSection(
    name="system_reboot_required",
    parse_function=parse_system_reboot_required,
)

check_plugin_system_reboot_required = CheckPlugin(
    name="system_reboot_required",
    service_name="System Reboot Required",
    discovery_function=discover_system_reboot_required,
    check_function=check_system_reboot_required,
    check_default_parameters=_DEFAULT_PARAMS,
    check_ruleset_name="system_reboot_required",
)
