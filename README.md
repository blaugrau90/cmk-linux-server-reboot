# System Reboot Required – Checkmk 2.4 Plugin

A Checkmk 2.4 MKP plugin that monitors Linux hosts for pending system reboots. It detects whether a reboot is required, how long it has been pending, and which packages triggered it — across all major Linux distributions.

**Requires:** Checkmk 2.4.0+ (CRE/CEE/CME) · Linux hosts with Checkmk agent · GPLv3 License

---

## Features

- Monitors every host with a single service: **System Reboot Required**
- Reports **how long** a reboot has been pending with configurable WARN/CRIT thresholds
- Supports all major Linux distributions via **multiple detection methods** (graceful degradation)
- Shows **detection method**, **time pending**, and **affected packages** in the service summary
- Immediate **CRIT** when a reboot is required but the pending-since timestamp is unknown

---

## Supported Distributions & Detection Methods

| Distribution | Detection Method | Details |
|---|---|---|
| Debian / Ubuntu | `/var/run/reboot-required` | Written by `apt` and `unattended-upgrades` |
| Debian / Ubuntu | `/var/run/reboot-required.pkgs` | Package list that triggered the reboot |
| Debian / Ubuntu (alt.) | `/run/reboot-required` | Fallback path on some systems |
| RHEL / CentOS 7+ | `needs-restarting -r` | Exit code 1 = reboot required |
| Rocky / AlmaLinux | `needs-restarting -r` | Same as RHEL |
| All RPM-based | `uname -r` vs. `rpm -q kernel --last` | Detects running kernel ≠ installed kernel |

Detection methods are tried in order. If one is unavailable (e.g. `needs-restarting` not installed), it is skipped silently.

---

## Installation

### Via Checkmk GUI (recommended)

1. Download `system_reboot_required-1.0.0.mkp` from the [Releases](https://github.com/blaugrau90/cmk-linux-server-reboot/releases) page
2. In Checkmk: **Setup → Extension Packages → Upload package**
3. Upload the `.mkp` file and click **Install**

### Via CLI (as site user)

```bash
mkp add system_reboot_required-1.0.0.mkp
mkp enable system_reboot_required
```

### Deploy the agent plugin to monitored hosts

The shell script must be installed on each monitored host:

```bash
# From the Checkmk site:
scp /omd/sites/<site>/local/share/check_mk/agents/plugins/system_reboot_required \
    root@<host>:/usr/lib/check_mk_agent/plugins/system_reboot_required

chmod 755 /usr/lib/check_mk_agent/plugins/system_reboot_required
```

Then run a service discovery:

```bash
cmk -II <hostname>
cmk -R
```

---

## Configuration

Navigate to **Setup → Services → Service monitoring rules → System Reboot Required**.

| Parameter | Default | Description |
|---|---|---|
| WARN after pending reboot for (hours) | 12 | Turns WARN when reboot has been pending for at least this many hours |
| CRIT after pending reboot for (hours) | 24 | Turns CRIT when reboot has been pending for at least this many hours |

**Note:** The CRIT threshold must be ≥ the WARN threshold. If a reboot is pending but the timestamp cannot be determined, the service turns CRIT immediately.

### Service states

| State | Condition |
|---|---|
| OK | No reboot pending |
| OK | Reboot pending for less than WARN threshold |
| WARN | Reboot pending for ≥ WARN hours |
| CRIT | Reboot pending for ≥ CRIT hours |
| CRIT | Reboot required, timestamp unknown |
| UNKNOWN | No data from agent plugin |

---

## How It Works

```
Checkmk Check Cycle
  └─ Agent plugin (shell script on monitored host)
       ├─ Checks /var/run/reboot-required       (Debian/Ubuntu)
       ├─ Reads /var/run/reboot-required.pkgs   (package list)
       ├─ Runs needs-restarting -r              (RHEL/CentOS/Rocky)
       └─ Compares uname -r vs rpm kernel       (RPM fallback)
  └─ Checkmk Section  <<<system_reboot_required>>>
       reboot_required: 1
       detection_method: reboot-required-file
       since_timestamp: <unix timestamp>
       packages: linux-image-generic, linux-headers-generic
  └─ Check plugin (system_reboot_required/agent_based/)
       ├─ Calculates age from timestamp
       └─ Compares against warn_hours / crit_hours thresholds
```

---

## File Structure

```
system_reboot_required/
├── agent_based/
│   └── system_reboot_required.py   # Check plugin: parse, discover, check
└── rulesets/
    └── system_reboot_required.py   # WATO ruleset: thresholds
agents/
└── plugins/
    └── system_reboot_required      # Shell script (runs on monitored host)
```

---

## Building from Source

Run as root on the Checkmk server:

```bash
# Deploy files to site (replace <site> with your site name)
SITE=<site>
install -m 755 agents/plugins/system_reboot_required \
    /omd/sites/$SITE/local/share/check_mk/agents/plugins/system_reboot_required
install -m 644 system_reboot_required/agent_based/system_reboot_required.py \
    /omd/sites/$SITE/local/lib/python3/cmk_addons/plugins/system_reboot_required/agent_based/system_reboot_required.py
install -m 644 system_reboot_required/rulesets/system_reboot_required.py \
    /omd/sites/$SITE/local/lib/python3/cmk_addons/plugins/system_reboot_required/rulesets/system_reboot_required.py

# Build MKP (as site user)
cp packages/system_reboot_required /omd/sites/$SITE/var/check_mk/packages/system_reboot_required
su - $SITE -c "mkp package /omd/sites/$SITE/var/check_mk/packages/system_reboot_required"
```

The resulting `.mkp` file will be in `/omd/sites/$SITE/var/check_mk/packages_local/`.

---

## License

GPLv3 — see [LICENSE](LICENSE)

## Author

Luca-Leon Hausdoerfer — [github.com/blaugrau90](https://github.com/blaugrau90)
