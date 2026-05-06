# AI Module — Smart Citizen Reporting System

## Overview

`app/services/ai_service.py` provides two capabilities:

1. **Zero-shot classification** — assigns a category to each new report using a local HuggingFace model (`facebook/bart-large-mnli`)
2. **Macedonian confirmation generation** — generates a citizen-facing confirmation message in Macedonian via the HF Inference API (free tier)

Both run inside `run_report_ai_pipeline` — a background thread that fires after report creation and never blocks the API response.

---

## Macedonian Confirmation 

### What it generates

Every new report receives an `ai_confirmation_text` field with a 3–4 sentence Macedonian message containing:

| Element | Example |
|---|---|
| Receipt confirmation | Вашата пријава е успешно примена |
| Category + priority | класифицирана како Инфраструктура со висок приоритет |
| Expected process | Очекувајте одговор во рок од 3–5 работни дена |
| Citizen advice | Препорачуваме да ја фотографирате локацијата |

### Priority translation

| DB value | Macedonian |
|---|---|
| `low` | низок |
| `medium` / `normal` | среден |
| `high` | висок |
| `urgent` | итен |
| `critical` | критичен |
| unknown string | shown as-is |
| `null` | omitted |

---

## Generated confirmation examples

### 1. Infrastructure — high priority
**Input:** "Голема дупка на улица Партизанска, опасна за возила."
**Category:** Infrastructure | **Priority:** high

```
Вашата пријава е успешно примена.
Вашата пријава е класифицирана kako Инфраструктура со висок приоритет.
Тимот за одржување на патишта ќе го разгледа проблемот во најкраток можен рок.
Препорачуваме да ја фотографирате локацијата и да избегнувате возење по оваа деница додека не се санира.
```

### 2. Communal Services — medium priority
**Input:** "Контејнерот на ул. Климент Охридски не е испразнет веќе 10 дена."
**Category:** Communal Services | **Priority:** medium

```
Вашата пријава е успешно примена.
Пријавата е класифицирана kako Комунални услуги со среден приоритет.
Комуналната служба ќе го испрати соодветниот тим во рок од 3–5 работни дена.
Доколку проблемот не се реши навреме, можете повторно да пријавите преку системот.
```

### 3. Safety — urgent priority + duplicate flag
**Input:** "Скршена улична ламба, темна улица, опасно за пешаците навечер."
**Category:** Safety | **Priority:** urgent | **Duplicate of:** #17

```
Вашата пријава е успешно примена.
Пријавата е класифицирана kako Безбедност со итен приоритет.
Забележавме дека оваа пријава може да е слична на пријава #17; нашиот тим ќе го разгледа тоа.
Ве молиме во меѓувреме да користите добро осветлени алтернативни рути.
```

### 4. Environment — low priority
**Input:** "Расфрлан отпад во паркот Гази Баба, влошува изгледот на зеленилото."
**Category:** Environment | **Priority:** low

```
Вашата пријава е успешно примена.
Пријавата е класифицирана kako Животна средина со низок приоритет.
Инспекторот за животна средина ќе го разгледа случајот во рок од 5–7 работни дена.
Ви благодариме за грижата за јавните простори.
```

### 5. No category, no priority — fallback template
**Input:** "Не знам каде да го пријавам ова, но нешто не е во ред кај фонтаната."
**Category:** null | **Priority:** null

```
Вашата пријава е успешно примена и ќе биде разгледана наскоро.
Очекувајте одговор во рок од 3–5 работни дена.
Ви благодариме за придонесот кон подобрување на нашата заедница.
```
*Deterministic fallback — shown when AI is unavailable or fields are missing.*

---

## Lifecycle

```
POST /api/v1/reports
  └─► create_report()            returns immediately  (ai_confirmation_text = null)
         │
         └─► BackgroundTask: run_report_ai_pipeline()
                  ├── classify_text()                  → sets category_id
                  ├── generate_confirmation_message()  → EN comment (optional)
                  └── generate_confirmation_mk()       → MK confirmation
                           ├── HF Inference API (Mistral-7B-Instruct) → AI text
                           └── any failure → _mk_fallback() → deterministic MK text
                                    │
                                    └── report.ai_confirmation_text = text
                                        db.commit()
```

`ai_confirmation_text` is `null` immediately after creation and populates within 5–30 seconds.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `AI_HF_INFERENCE_MODEL` | `mistralai/Mistral-7B-Instruct-v0.2` | Model for MK text generation |
| `AI_HF_INFERENCE_TIMEOUT_SECONDS` | `30` | HF API request timeout |
| `HF_API_TOKEN` | *(empty)* | Optional — get free token at huggingface.co/settings/tokens |

---

## Running tests

```bash
pytest tests/test_ai_confirmation_mk.py -v
```