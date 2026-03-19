# Sentinel-NAC: Ethics, Legal, and Authorized Use Statement

## Our Commitment

This project was built for **defensive, educational cybersecurity purposes only**.

The team — Yashvi Thakkar, Mantra Patel, Tirth Patel, and Dhruv Patel — developed
Sentinel-NAC to learn and demonstrate Zero Trust network access control concepts.

---

## Authorized Use Only

**You MAY use this system:**
- On networks and devices that you own personally.
- In your college lab environment with explicit permission from your institution.
- In a private home lab using your own router or mobile hotspot.
- For educational demonstrations in controlled settings with informed participants.

**You MUST NOT use this system:**
- On public Wi-Fi networks (cafés, airports, shopping centers, etc.)
- On your college or university's main production network without written authorization.
- On any network belonging to a third party without explicit written consent.
- To monitor, intercept, or block traffic to/from devices you do not own or control.
- To perform offensive attacks, credential theft, stealthy persistence, or exploitation.

---

## Legal Context

Unauthorized network monitoring, traffic interception, or device blocking may violate:
- The **IT Act, 2000** (India) — Sections 43, 65, 66, 66B
- **Computer Fraud and Abuse Act** (USA)
- **GDPR** (European Union) for privacy violations
- Your institution's **Acceptable Use Policy (AUP)**

Violations may result in academic disciplinary action, civil liability, or criminal prosecution.

---

## Technical Safeguards Built Into This Project

1. **Default enforcement mode is `simulation`** — no real network blocks are applied
   unless explicitly changed in the configuration file.

2. **Firewall mode requires `sudo`** — prevents accidental activation.

3. **The system does not:**
   - Steal credentials or session tokens
   - Perform man-in-the-middle attacks
   - Exfiltrate data from devices
   - Implement stealthy persistence mechanisms
   - Target devices outside the configured subnet

4. **All enforcement is host-based** — only affects traffic rules on the machine
   running Sentinel-NAC, not the router or other network devices.

---

## Responsible Disclosure

If you discover security vulnerabilities in this codebase, please report them
to the project team rather than exploiting them. This is a student project and
is not intended for production use.

---

## Declaration

By installing and running this software, you confirm that:

1. You are running it in an authorized, private environment.
2. All devices being monitored belong to you or you have explicit consent.
3. You understand and accept all legal responsibilities.
4. You will not use this software for unauthorized network monitoring.

---

*Sentinel-NAC was built as a learning exercise in defensive cybersecurity.
We stand firmly against unauthorized access, privacy violations, and malicious use
of network tools.*
