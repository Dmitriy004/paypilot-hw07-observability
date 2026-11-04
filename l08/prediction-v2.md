# V2 final-set forecast — before new independent holdout

2026-11-04. Окремий прогноз після виправлення H03 false-positive. V1 прогноз0d340b6 та його негативний clean результат6/7 збережені, а не переписані. Цей прогноз **поінформований** exploratory і v1 даними, не сліпий; v1 тепер належить до калібрування v2.

Фінальний v2 set SHA256:
`e9cf3e571e175b9c0d6c37a462032a229c7179ce3bfa35c00dbd66683e658d26`.
L03 set_hash: **e9cf3e571e17**. Source/data commit: **cf138cf**.
Модель anthropic/claude-haiku-5.5, reasoning off; fixture clock2026-09-15T10:00:00Z; summarize_after default8. Налаштування і репліки незмінні, порівнюється лише profile clean/lesson-08. Ніякі v2 вимірювання ще не відомі.

Єдина зміна runtime набору від v1 — H03 token threshold33306 (combined10-clean median19032 +75%), щоб дозволити нормальний knowledge lookup. Це operational cost guard, а не чутливий D15 detector. Пояснення і request IDs — [calibration-v2.md](calibration-v2.md).

| ID | Критерій | Clean прогноз | Lesson-08 прогноз |
|---|---|---|---|
| CONV-H01-BUDGET | median tokens≤47517 | PASS | PASS, відомий широкий поріг |
| CONV-H02-BUDGET | median tokens≤63449 | PASS | PASS, довгий сценарій лишається найбільш невпевненим |
| CONV-H03-BUDGET | median tokens≤33306 | PASS | PASS, тепер дозволена normal retrieval variance |
| **CONV-H04-BUDGET** | **median tokens≤47027** | **PASS** | **FAIL, D15** |
| CONV-H05-BUDGET | median tokens≤41135 | PASS | PASS |
| **COST-H06-EMPTY** | **identical calls≤1** | **PASS** | **FAIL, D14** |
| COST-CTRL-ACCOUNT | get_account викликається | PASS | PASS |

Очікую clean **7 з7**, lesson-08 **5 з7**; конкретні FAIL — **CONV-H04-BUDGET і COST-H06-EMPTY**. П'ять release cases по5 повторів, два daily cases по1. Ці54 нові діалоги виконуються послідовно в новому **чистому клоні після цього коміту**, не змішуються з попередніми повтореннями.

Залишковий ризик: H03 ширший і пропустить помірний replay; H04 може мати нову legitimate variance; cost PASS не оцінює consent/правильність write чи quality відповіді. Legitimate account control має лишитися зеленим. Нові невідповідності прогнозу фіксуються, набір цієї версії не підлаштовується під її holdout і жоден запуск не відкидається.
