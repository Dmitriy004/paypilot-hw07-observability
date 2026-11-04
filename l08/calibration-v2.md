# V2: H03 legitimate retrieval variance

V1 input set_hash4c125924888f і forecast0d340b6 не переписуються. Два його незалежні holdout прогони завершилися: lesson-08 **5/7 PASS** з очікуваними H04/H06 FAIL; clean **6/7 PASS**, неочікуваний **H03 FAIL**. Це один помилковий clean прогноз, а не успішні7/7.

Джерела: reports/l05_dialogs-lesson-08-20261104T181529.json і reports/l05_dialogs-clean-20261104T182329.json. Усі primary traces збережені; вони тепер є exploratory даними для v2, не її незалежним підтвердженням.

## Причина, доведена спанами

H03 clean-v1 tokens=[18877,18755,30052,23151,26191], median23151>22834. У всіх п'яти умовах active_defects порожній і context.replay_active=false.

- Run1: лише tool.check_dispute_eligibility,6 llm.call,18877 tokens; запити50d9925196794bb6…25cff68679c348f1.
- Run3: два tool.search_knowledge_base +check_dispute_eligibility,7 llm.call,30052 tokens; запити7617a463924e4b8b…40aad256201c4444.
- Run4: search_knowledge_base +check_dispute_eligibility,6 llm.call,23151 tokens; запити7ad6c5033e04422c…2864b3c453244fd5.

Отже відмінність — нормальна стратегія пошуку і розмір її контексту, не активний D15. Точний вхід/результат кожного tool span є у batch evidence/20261104T181609.677227Z, files000086…000110.

## Зміна до нових незалежних вимірювань

Об'єднані десять clean samples: [19028,22683,19036,18950,18684,18877,18755,30052,23151,26191]. Median=19032; max30052, тобто +57.9% до медіани. Для H03 обираємо явний запас **75%**, ceil(19032×1.75)=**33306**: він на10.8% вищий за найбільший спостережений legitimate run.

Це широкий operational guard грубої вартості, **не чутливий детектор D15**. Trade-off: більше невеликих replay пройде; чутливий детектор — H04 з незмінним47027 і D14 H06 з identical max1. Решта кейсів, репліки, модель/reasoning, clock, grader і compose незмінні. Не вимикаємо корисний knowledge lookup задля зеленого лічильника.

Regression test відтворив clean-v1 failure (RED); після зміни лише H03 threshold він має пройти. Окремий тест із H04 replay tokens має лишитися FAIL за graderом. Потім новий set_hash і **окремий forecast commit**, новий чистий клон та обидва повні27-dialog holdout прогони. Нові результати не відомі на момент вибору33306; старі результати не видаляються.
