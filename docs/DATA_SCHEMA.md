# Data schema Expense Splitter

Документ фиксирует пользовательскую YAML-схему данных Expense Splitter. Текущая версия схемы для покупок: `v2`.

## purchases.yaml

Файл содержит корневой объект:

```yaml
purchases:
  - id: p1
    date: '2026-06-18'
    purchase_name: Кофе
    amount: '150.00'
    payer: Павел
    participants:
      - Павел
      - Сергей
    category: Напитки
    comment: null
```

### Поля покупки v2

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `id` | string | да | Идентификатор покупки. |
| `date` | date/null | да | Дата покупки в формате `YYYY-MM-DD` или `null`. |
| `purchase_name` | string | да | Наименование покупки. Пустое значение нормализуется в `н/д`. |
| `amount` | decimal/string | да | Сумма покупки, должна быть больше нуля. |
| `payer` | string | да | Участник, оплативший покупку. |
| `participants` | list[string] | да | Участники, между которыми делится покупка. |
| `category` | string/null | нет | Категория покупки. |
| `comment` | string/null | нет | Комментарий к покупке. |

## Совместимость с v1

В v1 для наименования покупки использовалось поле `title`.

Правила совместимости:

- `purchase_name` является каноническим полем v2.
- `title` поддерживается только как legacy alias при чтении старого YAML.
- Если в YAML есть `title`, но нет `purchase_name`, приложение возвращает `purchase_name = title`.
- Если отсутствуют и `title`, и `purchase_name`, приложение возвращает `purchase_name = "н/д"`.
- Новая запись YAML всегда использует `purchase_name` и не записывает `title`.

## participants.yaml

Схема участников и групп на этапе P1.0 не менялась:

```yaml
participants:
  - name: Павел
groups:
  - name: 809 кабинет
    members:
      - Павел
```
