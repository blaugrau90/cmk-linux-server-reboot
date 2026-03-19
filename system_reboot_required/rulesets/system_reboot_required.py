# system_reboot_required - CheckMK WATO ruleset
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

from cmk.rulesets.v1 import Help, Title
from cmk.rulesets.v1.form_specs import (
    DefaultValue,
    DictElement,
    Dictionary,
    Integer,
    validators,
)
from cmk.rulesets.v1.rule_specs import CheckParameters, HostCondition, Topic


def _validate_thresholds(value: dict) -> None:
    warn = value.get("warn_hours", 12)
    crit = value.get("crit_hours", 24)
    if crit < warn:
        raise validators.ValidationError(
            "CRIT threshold must be greater than or equal to WARN threshold."
        )


def _parameter_form() -> Dictionary:
    return Dictionary(
        title=Title("System Reboot Required"),
        help_text=Help(
            "Configure thresholds for how long a pending reboot is tolerated before "
            "the service changes state. A reboot with an unknown pending-since timestamp "
            "always triggers CRIT immediately, regardless of these thresholds."
        ),
        elements={
            "warn_hours": DictElement(
                parameter_form=Integer(
                    title=Title("WARN after pending reboot for (hours)"),
                    help_text=Help(
                        "The service will turn WARN when a reboot has been pending for "
                        "at least this many hours. Set to 0 to warn immediately."
                    ),
                    prefill=DefaultValue(12),
                    custom_validate=(validators.NumberInRange(min_value=0),),
                ),
                required=True,
            ),
            "crit_hours": DictElement(
                parameter_form=Integer(
                    title=Title("CRIT after pending reboot for (hours)"),
                    help_text=Help(
                        "The service will turn CRIT when a reboot has been pending for "
                        "at least this many hours. Must be >= WARN threshold."
                    ),
                    prefill=DefaultValue(24),
                    custom_validate=(validators.NumberInRange(min_value=0),),
                ),
                required=True,
            ),
        },
        custom_validate=(_validate_thresholds,),
    )


rule_spec_system_reboot_required = CheckParameters(
    title=Title("System Reboot Required"),
    topic=Topic.OPERATING_SYSTEM,
    name="system_reboot_required",
    parameter_form=_parameter_form,
    condition=HostCondition(),
)
