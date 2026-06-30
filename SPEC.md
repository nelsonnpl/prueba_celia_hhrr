# RIU360 — Technical Specification Document
## Corporate Assessment Portal for RIU Hotels & Resorts

**Document Version:** 1.0  
**Date:** June 2024  
**Author:** HR Technology & Talent Acquisition Team  
**Status:** Production-Ready

---

## 1. Executive Summary

RIU360 is a secure, web-based candidate assessment platform designed to evaluate strategic thinking, industry knowledge, and analytical capabilities of candidates applying for management and senior roles within RIU Hotels & Resorts.

The platform simulates a real-world business case scenario, requiring candidates to formulate a strategic revenue recovery plan for an underperforming 5-star property. The system enforces assessment integrity through multiple layers of behavioral monitoring and anti-fraud protocols.

---

## 2. Objectives

| Objective | Description |
|-----------|-------------|
| **Standardization** | Every candidate receives the identical assessment experience, regardless of location or device |
| **Integrity** | Multi-layered anti-fraud system detects AI-generated content, copy-paste injection, and external assistance |
| **Candidate Experience** | Clean, professional, RIU-branded interface that reflects the company's luxury hospitality identity |
| **Data Collection** | Comprehensive telemetry for HR review, including behavioral patterns and risk scoring |
| **Compliance** | GDPR-aligned data handling; all data persists locally on controlled infrastructure |

---

## 3. User Flow

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   LOGIN     │────>│  RULES & ACCEPT  │────>│   EVALUATION     │────>│  CONFIRMATION   │
│             │     │                  │     │                  │     │                 │
│ Candidate ID│     │ Read guidelines  │     │ Case study brief │     │ Submission      │
│ Test Code   │     │ Check checkbox   │     │ Write response   │     │ Summary         │
│             │     │ Accept terms     │     │ Timer active     │     │ Close session   │
│ NO security │     │ NO security      │     │ SECURITY ACTIVE  │     │ NO security     │
└─────────────┘     └──────────────────┘     └──────────────────┘     └─────────────────┘
```

### 3.1 Login Screen
- Candidate enters **Candidate ID** (or email) and **Test Access Code**
- Server validates credentials against pre-loaded registry
- On success, generates a unique session token
- **No security restrictions active at this stage**

### 3.2 Rules & Conditions Screen
- Displays the candidate's name, ID, and session token
- Lists 5 assessment rules with clear language:
  1. Time Limit (60 minutes)
  2. Original Work Only (no AI, no copy-paste)
  3. Restricted Actions (right-click, shortcuts, tab switching monitored)
  4. Word Count (400-600 words)
  5. One Submission Only
- Candidate must check an agreement checkbox to enable the "Begin Assessment" button
- **No security restrictions active at this stage**

### 3.3 Evaluation Screen
- Two-panel layout: Case Study (left) + Response textarea (right)
- Header with logo, language selector, candidate info, and help button
- Timer bar with elapsed time, word count, and alert badge
- **ALL security restrictions activate upon entering this view**

### 3.4 Confirmation Screen
- Success confirmation with submission summary
- Displays: candidate name, submission ID, word count, time elapsed
- Option to close session and return to login

---

## 4. Design System

### 4.1 Brand Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `riu-red` | `#D2232A` | Primary brand color, logo, CTAs, active states |
| `riu-redDark` | `#B01C22` | Button hover state |
| `riu-gold` | `#CA9C4E` | Accent color, decorative elements, secondary highlights |
| `riu-charcoal` | `#1A1A1A` | Primary text, headings |
| `riu-gray` | `#F8F9FA` | Backgrounds, input fields |
| `riu-grayMid` | `#6C757D` | Secondary text, labels |
| `riu-grayLight` | `#E8E6E3` | Borders, dividers |
| `riu-cream` | `#FAF9F7` | Warm background tint |
| `riu-sand` | `#F0EDE8` | Card backgrounds, warm accents |

### 4.2 Typography

| Element | Font | Weight | Size |
|---------|------|--------|------|
| Display headings | Cormorant Garamond | 600-700 | 28-60px |
| Body text | Inter | 400-500 | 13-14px |
| Labels & tags | Inter | 600-700 | 10-11px (uppercase) |
| Monospace (timer, counters) | System monospace | 600 | 12-14px |

### 4.3 Spacing & Layout
- Border radius: 6px (cards), 10px (large containers)
- Shadows: Three tiers (riu, riu-md, riu-lg)
- Max content width: 1400px
- Mobile breakpoint: `lg` (1024px)
- Panel layout: Side-by-side on desktop, stacked on mobile (response panel first)

### 4.4 Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| `< 640px` | Full mobile: stacked panels, compact header, hamburger menu |
| `640px - 1024px` | Tablet: stacked panels with more padding |
| `> 1024px` | Desktop: two-panel layout, full header |

---

## 5. Security & Anti-Fraud System

### 5.1 When Active
Security restrictions are **ONLY active during the Evaluation view** (Phase 3). They are disabled during Login, Rules, and Confirmation screens.

### 5.2 Client-Side Protections

| Protocol | Implementation | Telemetry |
|----------|---------------|-----------|
| Right-click block | `contextmenu` event prevention | `rightClickAttempts` |
| Keyboard shortcuts | Block Ctrl+C/V/X/A/S/P/F12/U/F, PrintScreen, Cmd+Shift+S/3/4/5 | `blockedShortcuts` |
| Paste block | `paste` event on textarea | `pasteAttemptsCount` |
| Keystroke tracking | `keydown` event on textarea | `totalKeystrokes` |
| Tab switch detection | `visibilitychange` + `blur` events | `tabSwitchesCount` |
| Drag & drop block | `dragover`/`drop` prevention on textarea | — |
| DevTools detection | Window dimension threshold monitoring | `blockedShortcuts` |
| Print prevention | `beforeprint` event + CSS `@media print` | — |
| Screenshot block | PrintScreen key interception + clipboard clearing | `screenshotAttempts` |
| Screen share block | `getDisplayMedia` API override | — |
| Blur overlay | White overlay when window loses focus | — |

### 5.3 Honeypot Text Injection
- Invisible text embedded in the case study (CSS `font-size: 0px`)
- Contains prompt injection in English and French targeting AI models
- Keyword: `anturio`
- If detected in submission → `honeypotTriggered: true` (50-point risk penalty)

### 5.4 Risk Score Calculation

| Factor | Points | Condition |
|--------|--------|-----------|
| Honeypot triggered | +50 | Text contains "anturio" |
| Keystroke anomaly | +25 | Character count > 2x keystroke count |
| Tab switches > 10 | +10 | Excessive context switching |
| Tab switches > 5 | +5 | Moderate context switching |
| Paste attempts | +5 each | Any paste attempt logged |
| Fast writing | +10 | >500 chars/min sustained |
| No keystrokes with text | +30 | Impossible without paste |

**Max score: 100**  
**Suspicious flag:** `true` if `honeypotTriggered` OR `isKeystrokeAnomaly`

---

## 6. API Specification

### 6.1 `POST /api/login`

**Request:**
```json
{
  "candidateId": "CAND-2024-001",
  "testCode": "RIU-PRUEBA-2024"
}
```

**Response (200):**
```json
{
  "success": true,
  "candidate": {
    "id": "CAND-2024-001",
    "name": "Maria Garcia",
    "email": "maria.garcia@riu.com"
  },
  "sessionToken": "a1b2c3...",
  "loginTimestamp": "2024-06-30T21:00:00Z"
}
```

### 6.2 `POST /api/submit`

**Request:**
```json
{
  "candidateId": "CAND-2024-001",
  "sessionToken": "a1b2c3...",
  "essayResponse": "Full essay text...",
  "wordCount": 520,
  "timeSpentMinutes": 35,
  "tabSwitchesCount": 2,
  "pasteAttemptsCount": 0,
  "totalKeystrokes": 2840,
  "rightClickAttempts": 1,
  "blockedShortcuts": 0,
  "startTime": "2024-06-30T21:00:00Z",
  "endTime": "2024-06-30T21:35:00Z"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Evaluation submitted successfully.",
  "submissionId": "uuid-v4"
}
```

### 6.3 `GET /api/admin/submissions`

Returns an array of all submissions with telemetry and analysis data (without essay text for overview).

---

## 7. Data Persistence

All data is stored in local JSON files:

| File | Content |
|------|---------|
| `data/candidates.json` | Pre-loaded candidate registry |
| `data/submissions.json` | All submitted evaluations with telemetry |

### 7.1 Submission Record Schema

```json
{
  "id": "uuid",
  "candidateId": "string",
  "sessionToken": "string",
  "essayResponse": "string",
  "wordCount": "number",
  "timeSpentMinutes": "number",
  "submittedAt": "ISO 8601",
  "telemetry": {
    "tabSwitchesCount": "number",
    "pasteAttemptsCount": "number",
    "totalKeystrokes": "number",
    "rightClickAttempts": "number",
    "blockedShortcuts": "number",
    "startTime": "ISO 8601",
    "endTime": "ISO 8601",
    "charCount": "number"
  },
  "analysis": {
    "honeypotTriggered": "boolean",
    "isKeystrokeAnomaly": "boolean",
    "isSuspicious": "boolean",
    "riskScore": "number (0-100)"
  }
}
```

---

## 8. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, Tailwind CSS (CDN), Vanilla JavaScript |
| Backend | Python 3.12+, Flask |
| Persistence | JSON file storage |
| Fonts | Google Fonts (Inter, Cormorant Garamond) |
| Deployment | Local server (localhost:3456) |

---

## 9. Candidate Test Accounts

| Candidate | ID | Email | Test Code |
|-----------|-----|-------|-----------|
| Maria Garcia | CAND-2024-001 | maria.garcia@riu.com | RIU-PRUEBA-2024 |
| Jean Dupont | CAND-2024-002 | jean.dupont@consulting.fr | RIU-PRUEBA-2024 |
| Anna Schmidt | CAND-2024-003 | anna.schmidt@riu.de | RIU-PRUEBA-2024 |

---

## 10. Running the Platform

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python server.py

# Access at
http://localhost:3456
```

---

## 11. Future Enhancements (Backlog)

| Priority | Enhancement |
|----------|------------|
| P1 | Multi-language support (EN/FR/ES/DE) for case study content |
| P1 | Time-limit enforcement (auto-submit at 60 minutes) |
| P2 | Admin dashboard with submission review UI |
| P2 | Email notifications for candidate results |
| P2 | Candidate registration flow (self-service) |
| P3 | Multiple case study variants (randomized) |
| P3 | Video response capability |
| P3 | Integration with RIU HRIS (Workday/SAP SuccessFactors) |
| P3 | SSL/TLS encryption for production deployment |
| P3 | Rate limiting and brute-force protection |

---

*Document prepared by the RIU Hotels & Resorts HR Technology Team.*
*For technical questions, contact: assessment-support@riu.com*
