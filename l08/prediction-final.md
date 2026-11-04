# Фінальний прогноз — ДО незалежних контрольних прогонів

Дата 2026-11-04. Прогноз поінформований exploratory калібруванням; це **не сліпий прогноз**. Початковий прогноз/протокол збережені у коміті8b85edf, негативний результат H01 і зміна до H04 задокументовані окремо, історія не переписувалася.

Фінальний `sets/l05_dialogs.jsonl` SHA256:
`4c125924888fd3140a2a9d6f5117fb12f8a541100c4994ddda2237843d2e5182`.
L03 `set_hash`: **`4c125924888f`**. Будь-яка зміна набору після цього потребує нового прогнозу ДО нового прогону; старий прогноз не підправляється під результат.

Модель `anthropic/claude-haiku-5.5`, reasoning off, clock2026-09-15T10:00:00Z. Compose явно передає model/reasoning; сумаризація — стандартний поріг8 стенду. Між confirmatory прогонами міняється **лише profile** clean ↔ lesson-08; репліки, бюджети, модель, clock і grader незмінні. Кожен token-case5 повторів, daily cases1.

| Конкретний ID | Заморожений критерій | Очікую clean | Очікую lesson-08 |
|---|---|---|---|
| CONV-H01-BUDGET | median dialog tokens ≤47517 | PASS | PASS — +20% нечутливий до помірного D15, це відомий пропуск |
| CONV-H02-BUDGET | median dialog tokens ≤63449 | PASS | PASS; довгий10-кроковий діалог після summary — головне джерело невпевненості, може дати додаткове падіння |
| CONV-H03-BUDGET | median dialog tokens ≤22834 | PASS | PASS |
| **CONV-H04-BUDGET** | **median dialog tokens ≤47027** | **PASS** | **FAIL**, D15 збільшує dialog tokens понад5% запас |
| CONV-H05-BUDGET | median dialog tokens ≤41135 | PASS | PASS |
| **COST-H06-EMPTY** | **identical_tool_calls_max ≤1** | **PASS** | **FAIL**, D14 повторює однаковий get_transactions для CUS-0003 |
| COST-CTRL-ACCOUNT | get_account викликається | PASS | PASS — легітимне питання має лишитися доступним |

Отже, очікую рівно два червоні кейси lesson-08: **CONV-H04-BUDGET та COST-H06-EMPTY**, не класи сценаріїв. Очікуваний рахунок clean7 з7, lesson-085 з7. Усі додаткові падіння або пропуски будуть названі по IDs і пояснені первинними трейсами, без повторів «до потрібного результату».

H04 exploratory calibration не є holdout: clean median44787 [44337–45645], defect median53464 [53232–54083], chosen47027. У final holdout ці значення будуть отримані заново з чистого клону; набір не переналаштовується після результату.

| Залишковий ризик | Тригер / вплив | Наявний контроль | Джерело еталону | Межа впевненості |
|---|---|---|---|---|
| Дешевий неправильний текст | Зміна reason/deadline без перевищення бюджету | B3 presence check, не universal judge | seed engine + corpus | Потрібна L09 quality evaluation |
| Варіативність token budget | Інша допустима tool strategy може підняти медіану | runs5, H04 margin5%, clean holdout | Власний exploratory baseline | Не обіцяє нуль false positives або виявлення кожного replay |
| Наївна дедуплікація | Легітимний повтор після зміни даних / transient error | H06 лише стабільний empty-result case, account control | Власний operational contract | Freshness/error-aware implementation ще не перевірено |
| Неправомірний irreversible write | Неправильний create_dispute/send_statement може бути дешевим | Cost checks не є blocking safety checks | rules engine / фактична БД | Потрібні незалежні pre-write checks, вимір їх latency та legitimate breakage scenario |

Цей файл комітиться окремо до confirmatory. Публікація й LMS submission ще не виконувалися.
