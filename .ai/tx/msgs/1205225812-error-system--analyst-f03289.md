---
to: deep-research/analyst
from: system
type: error
msg-id: f03289
timestamp: 2025-12-05T22:58:12.659Z
---

# ⚠️ Message Rejected - Action Required

Your previous message (`iteration2-complete`) was rejected and **NOT delivered**.

**Reason**: rearmatter-invalid
**Attempt**: 1/3

## Validation Errors

- Grade must be one of [A, B, C, D, F], got 'A+'

## How to Fix

Rearmatter must be valid YAML:

```yaml
---
grade: A
confidence: 0.95
speculation:
  42: "description of speculation on line 42"
gaps:
  15: "missing information on line 15"
assumptions:
  8: "assumption made on line 8"
---
```

**Common mistakes:**
- Line numbers must be **integers** (not strings like "89")
- Use proper YAML indentation (2 spaces)
- Don't quote the line numbers
- Line numbers reference lines in your message body (not including frontmatter)

## Next Steps

1. Fix the errors above
2. Resend your corrected message using the Write tool
3. You have **2** attempt(s) remaining
