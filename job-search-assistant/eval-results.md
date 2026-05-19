# Evaluation Results

_Generated: 2026-04-14T01:54:06.705Z_

## Extraction Spot-Check

Manually reviewed 3 postings against extracted JSON:

### AI Application Manager at LITENS AUTOMOTIVE GROUP
- Required skills extracted: 10
- Preferred skills extracted: 0
- Salary listed: no
- Company research: populated
- **Your accuracy notes:** _fill this in after reviewing_

### AI Developer ‒ LLM Integration & Java / Spring at CGI
- Required skills extracted: 10
- Preferred skills extracted: 2
- Salary listed: yes
- Company research: populated
- **Your accuracy notes:** _fill this in after reviewing_

### AI Engineer at KUBRA
- Required skills extracted: 7
- Preferred skills extracted: 2
- Salary listed: no
- Company research: populated
- **Your accuracy notes:** _fill this in after reviewing_

## Scoring Check

_Fill in after running Phase 3 on 3 postings at different fit levels._

| Posting | Score | Label | Agree? | Notes |
|---------|-------|-------|--------|-------|
| | | | | |
| | | | | |
| | | | | |

## Consistency Check

_Run Phase 3 twice on the same posting and fill in:_

- Run 1 score: 
- Run 2 score: 
- Were recommendations consistent? 
- Notable differences: 

## Failure Analysis

See console output for documented failures. Summary:

1. **PDF Image-Based Extraction** — pdf2json fails on image PDFs, LLM receives empty text
2. **Naive Skill Matching** — string contains() causes false positives (Java/JavaScript)
3. **Resume Extraction at Low Char Count** — spaced characters reduce information density
4. **Missing Salary Data** — Canadian postings rarely list salary
5. **LLM Hallucination on Empty Input** — no guard against near-empty text input

## Overall Observations

_Fill in after running full evaluation:_

- What the system does well: 
- Where it falls short: 
- Would you trust it in a real job search? 