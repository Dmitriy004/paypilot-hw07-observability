# Попередній прогноз до першого платного прогону

2026-11-04; жодних живих L08/HW07 запитів ще не виконано. Прогноз поінформований текстом уроку, кодом дефектів і попереднім фідбеком, не сліпий.

Exploratory dataset hash (L03): `7b3d2a38ceac`; повний hash буде записаний після заморожування порогів. Початкові 1000000 tokens_total не є фінальними порогами. Перед confirmatory буде інший окремий коміт прогнозу на фінальному наборі.

| Умова / кейс | Прогноз |
|---|---|
| B1 baseline | 5 з 5 проходять tool_called і identical_tool_calls_max=1 |
| B1 clean+D14 | 0 з 5 проходять identical_tool_calls_max=1; usage cost занижує фактичні retry-виклики |
| B2 baseline | first-call input кроку 6 за медіаною 5 ≤6500 |
| B2 lesson-08 | first-call input кроку 6 за медіаною 5 >6500; replay збільшує токени й ціну |
| B3 baseline, summarize_after=2 | 5 з 5 summary зберігають TX-0401 і duplicate_charge |
| B3 lesson-05, summarize_after=2 | 0 з 5 summary зберігають обидві сутності; перша втрата в agent.summarize, не фінальній відповіді |
| COST-H06-EMPTY clean / lesson-08 | clean PASS, lesson-08 FAIL на identical_tool_calls_max=1 |
| COST-CTRL-ACCOUNT clean / lesson-08 | обидва PASS: легітимний get_account не блокується |
| CONV-H01-BUDGET…CONV-H05-BUDGET | exploratory clean PASS через широкий ліміт; після заздалегідь заданої калібровки +20% очікую clean PASS, lesson-08 FAIL на tokens_total; фінальний прогноз назве кожний ID окремо |

Міграція B4: порівняти обидві моделі, B1/B2, обидві умови по5. Гіпотеза: Haiku дешевший за діалог; PASS/FAIL B1 не зміниться, B2 може змінитися через tokenizer/поведінку, тому 6500 не переноситься як універсальна межа. Вартість span-тарифів повинна збігатися з provider з урахуванням кешу; summarization має рахуватися окремо від kit $trace (llm.call only).

Усі спроби й незбіги прогнозу залишаються у доказах. Ліміт нових платних витрат $1, без автоматичних поповнень. Баланс аккаунта не публікується.
