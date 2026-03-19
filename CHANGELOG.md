# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — next release

### Fixed
- **False positive reboot alert on Debian/Ubuntu hosts** (`rpm-kernel-mismatch`)
  - Detection method 4 (RPM kernel comparison) was triggering on Debian-based systems
    where `rpm` is installed but not the primary package manager.
  - `rpm -q kernel --last` returns `"package kernel is not installed"` on Debian, causing
    `awk '{print $1}'` to extract `"package"` — which never matches `uname -r`.
  - Fix: Method 4 is now skipped on any system where `dpkg` is present.
  - Affected file: `agents/plugins/system_reboot_required`

---

## [1.0.0] — 2026-03-20

- Initial release
