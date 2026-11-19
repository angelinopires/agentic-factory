---
name: humanizer-compact
version: 1.0.0
description: |
  Remove AI tells from SHORT text (≤150 words): form fields, ATS answers, captions,
  taglines, microcopy, product descriptions, single paragraphs. Carries only the
  patterns that actually fire in short prose — AI vocabulary, filler, hedging,
  rule of three, em dashes, sycophancy, generic conclusions, signposting,
  promotional language, vague attributions. For articles, essays, cover letters
  and anything over ~150 words, use the full `humanizer` skill instead.
license: MIT
allowed-tools:
  - Read
  - Edit
---

# Humanizer (compact)

Short-text variant of `humanizer` v2.5.1. Same source (Wikipedia's "Signs of AI
writing"), reduced to the ten patterns that occur in a paragraph or less.

**Scope:** patterns only. This skill owns no voice. The calling skill supplies
tone and brand voice — do not flatten the caller's voice toward a neutral default.

**Language:** patterns apply in English and PT-BR alike. The em dash rule is
stricter in PT-BR, where `—` reads as AI on sight.

**Escalate:** if the text is over ~150 words, or is an article, essay, or cover
letter, stop and use the full `humanizer` skill.

## Patterns

**1. AI vocabulary** — delve, crucial, pivotal, key (adj), landscape (abstract),
tapestry, testament, underscore, highlight (verb), showcase, enhance, foster,
align with, interplay, intricate, vibrant, valuable, enduring, garner,
additionally. In PT-BR: crucial, fundamental, robusto, cenário, panorama,
impulsionar, potencializar, alavancar.
→ Use the plain word or cut the sentence.

**2. Filler phrases** — "in order to" → "to"; "due to the fact that" → "because";
"at this point in time" → "now"; "has the ability to" → "can"; "it is important
to note that" → cut entirely.

**3. Excessive hedging** — could potentially possibly, might have some effect,
it could be argued that. Keep one hedge maximum, drop the rest.

**4. Rule of three** — forced triads ("innovation, inspiration, and insights").
In a short paragraph a triad is almost always padding. Cut to the one that
carries information.

**5. Em dash overuse** — rewrite with a comma, a period, or parentheses.
More than one `—` in a short paragraph is a hard fail.

**6. Sycophantic tone** — "Great question", "I'm truly excited", "I'd be thrilled",
"absolutely love". Enthusiasm stated is weaker than enthusiasm demonstrated by a
specific detail.

**7. Generic positive conclusions** — "the future looks bright", "excited to
contribute to your journey", "a great step forward". Replace with a concrete fact
or delete the closing sentence. A short text does not need a closer.

**8. Signposting** — "let's dive in", "here's what you need to know", "I want to
highlight". Do the thing instead of announcing it.

**9. Promotional language** — boasts, vibrant, rich (figurative), groundbreaking,
renowned, stunning, seamless, cutting-edge, nestled, in the heart of.
→ State what the thing actually does.

**10. Vague attributions** — "industry reports", "experts argue", "many believe",
"it's well known that". Either name the source or drop the claim. Never invent a
source or a number to fill the gap.

## Process

1. Rewrite, fixing every hit above while preserving meaning and the caller's voice.
2. Self-audit in one line: "what still reads as AI here?"
3. Apply that fix and return the final text.

Return the final text only, plus a one-line note of what was changed. No draft
versions, no before/after table — the caller is mid-workflow and does not need them.
