# Frontend API Integration Guide (MVP)

Подробный контракт текущего backend API для frontend.
Покрывает: авторизацию, профиль, подписки, посты, лайки, загрузку медиа.

## 1. Общие правила интеграции

### 1.1 Базовые URL

- API base: `/api/v1`
- Swagger: `/docs`
- Health-check: `GET /api/v1/health`

Пример локального base URL:

- `http://localhost:8000/api/v1`

### 1.2 Формат авторизации

Для защищенных ручек всегда передавать:

```http
Authorization: Bearer <access_token>
```

Если токена нет или он невалидный:

- статус: `401`
- формат ошибки: `{"detail": "..."}`.

### 1.3 Формат ошибок

Все бизнес-ошибки возвращаются в одном формате:

```json
{
  "detail": "Текст ошибки"
}
```

### 1.4 Формат дат

Поля типа `created_at` возвращаются как ISO datetime.
Формат вида “5 минут назад” считается на frontend.

### 1.5 Про `204 No Content`

Для ряда действий backend возвращает только статус `204` без тела:

- follow / unfollow
- like / unlike
- delete post

Это означает, что действие выполнено успешно.
`success: true` в теле здесь не предусмотрен.

### 1.6 Идемпотентность действий

- Повторный `follow` на уже подписанного пользователя возвращает `204` (без ошибки).
- Повторный `unfollow` для отсутствующей подписки тоже возвращает `204`.
- Повторный `like`/`unlike` работает аналогично и не падает ошибкой.

Это удобно для frontend: можно не строить сложную защиту от повторных кликов на уровне API.

## 2. Auth (регистрация и вход)

## 2.1 `POST /users/signup`

### Когда вызывать

- На экране регистрации.

### Request

Headers:

- `Content-Type: application/json`

Body:

```json
{
  "login": "user_login",
  "password": "strong123",
  "name": "Display Name"
}
```

### Успешный ответ

- Статус: `201`

```json
{
  "id": "9e8f3e2c-5f2a-4e4f-8f47-0a4bbef2a0bc",
  "login": "user_login",
  "name": "Display Name",
  "created_at": "2026-04-10T15:21:36.522841+00:00"
}
```

### Валидации

- `login`: минимум 3 символа, без пробелов
- `password`: минимум 8 символов
- `name`: минимум 2 символа

### Возможные ошибки

- `400`: ошибка валидации
- `409`: пользователь с таким логином уже существует

## 2.2 `POST /users/login`

### Когда вызывать

- На экране входа.

### Request

Headers:

- `Content-Type: application/json`

Body:

```json
{
  "login": "user_login",
  "password": "strong123"
}
```

### Успешный ответ

- Статус: `200`

```json
{
  "access_token": "<jwt>"
}
```

### Возможные ошибки

- `401`: неверный логин или пароль

### Как frontend должен использовать результат

1. Сохранить `access_token` (например, localStorage/secure storage).
2. Добавлять token во все защищенные запросы.
3. После логина сразу вызвать `GET /users/me` и инициализировать профиль сессии.

## 3. Профиль пользователя

## 3.1 Модель профиля (`UserProfileResponse`)

```json
{
  "id": "uuid",
  "nickname": "Никнейм",
  "avatar_url": "http://localhost:9000/royality-media/profile/...jpg",
  "bio": "Обо мне",
  "level": 7,
  "posts_count": 12,
  "followers_count": 5,
  "is_following": false,
  "created_at": "2026-04-10T15:21:36.522841+00:00"
}
```

Расшифровка полей:

- `id`: ID пользователя
- `nickname`: отображаемое имя в UI профиля
- `avatar_url`: URL аватара (может быть `null`)
- `bio`: текст “Обо мне” (может быть `null`)
- `level`: уровень пользователя
- `posts_count`: количество постов пользователя
- `followers_count`: количество подписчиков пользователя
- `is_following`: подписан ли текущий авторизованный пользователь на этот профиль
- `created_at`: дата регистрации

Важно:

- Для собственного профиля (`/users/me` или `/users/{my_id}`) `is_following` всегда `false`.

## 3.2 `GET /users/me`

### Когда вызывать

- После логина
- При открытии экрана “Мой профиль”
- После обновления токена/рефреша приложения

### Request

Headers:

- `Authorization: Bearer <access_token>`

### Успешный ответ

- Статус: `200`
- Body: `UserProfileResponse`

### Возможные ошибки

- `401`: нет токена/невалидный токен
- `404`: профиль не найден

## 3.3 `PUT /users/me`

### Когда вызывать

- При сохранении редактирования профиля.

### Request

Headers:

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

Body:

```json
{
  "nickname": "Новый ник",
  "avatar_url": "http://localhost:9000/royality-media/profile/9e8f.../a1b2.jpg",
  "bio": "Текст обо мне",
  "level": 10
}
```

`avatar_url` и `bio` можно передавать `null`.

### Успешный ответ

- Статус: `200`
- Body: обновленный `UserProfileResponse`

### Валидации

- `nickname`: 2..128 символов
- `level`: 1..100
- `avatar_url`: валидный `http/https` URL или `null`
- `bio`: максимум 1000 символов или `null`

### Возможные ошибки

- `400`: ошибка валидации
- `401`: нет/невалидный токен
- `404`: профиль не найден

## 3.4 `GET /users/{user_id}`

### Когда вызывать

- При открытии чужого профиля.

### Request

Headers:

- `Authorization: Bearer <access_token>`

### Успешный ответ

- Статус: `200`
- Body: `UserProfileResponse`

### Поведение `is_following`

- `true`: текущий пользователь подписан на `user_id`
- `false`: не подписан

### Возможные ошибки

- `400`: некорректный `user_id`
- `401`: нет/невалидный токен
- `404`: профиль не найден

## 3.5 `POST /users/{user_id}/follow`

### Когда вызывать

- Нажатие кнопки “Подписаться” на чужом профиле.

### Request

Headers:

- `Authorization: Bearer <access_token>`

Body: отсутствует

### Успешный ответ

- Статус: `204`
- Тело: отсутствует

### Возможные ошибки

- `400`: некорректный `user_id` или попытка подписаться на самого себя
- `401`: нет/невалидный токен
- `404`: целевой пользователь не найден

### Как обновлять UI после успеха

Вариант A (оптимистично):

- `is_following = true`
- `followers_count += 1`

Вариант B (синхронно с backend):

- после `204` вызвать `GET /users/{user_id}` и взять свежие `is_following/followers_count`.

## 3.6 `DELETE /users/{user_id}/follow`

### Когда вызывать

- Нажатие кнопки “Отписаться”.

### Request

Headers:

- `Authorization: Bearer <access_token>`

Body: отсутствует

### Успешный ответ

- Статус: `204`
- Тело: отсутствует

### Возможные ошибки

- `400`: некорректный `user_id` или попытка отписаться от самого себя
- `401`: нет/невалидный токен
- `404`: целевой пользователь не найден

### Как обновлять UI после успеха

Вариант A (оптимистично):

- `is_following = false`
- `followers_count = max(0, followers_count - 1)`

Вариант B:

- после `204` запросить `GET /users/{user_id}`.

## 4. Посты

## 4.1 Модель поста (`PostResponse`)

```json
{
  "id": "2e6e28cc-77d9-4b89-ae90-b3cecf13088f",
  "text": "Текст поста",
  "medias": [
    "http://localhost:9000/royality-media/post/9e8f.../f4c9.jpg"
  ],
  "disable_comments": false,
  "author": {
    "id": "9e8f3e2c-5f2a-4e4f-8f47-0a4bbef2a0bc",
    "name": "Display Name",
    "avatar_url": null
  },
  "likes_count": 1,
  "is_liked": true,
  "created_at": "2026-04-10T16:01:10.100145+00:00"
}
```

Расшифровка полей:

- `id`: ID поста
- `text`: текст поста
- `medias`: список URL изображений поста
- `disable_comments`: флаг запрета комментариев (комментарии пока не реализованы)
- `author.id`: ID автора
- `author.name`: отображаемое имя автора
- `author.avatar_url`: URL аватара автора (может быть `null`)
- `likes_count`: количество лайков поста
- `is_liked`: поставил ли текущий авторизованный пользователь лайк этому посту
- `created_at`: время создания поста

## 4.2 `POST /posts` (создание поста)

### Когда вызывать

- На форме создания поста.

### Request

Headers:

- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

Form-data:

- `text` (string, обязательно)
- `image` (file, обязательно)
- `disable_comments` (bool, опционально, default `false`)

Пример через `curl`:

```bash
curl -X POST "http://localhost:8000/api/v1/posts" \
  -H "Authorization: Bearer <token>" \
  -F "text=Мой первый пост" \
  -F "disable_comments=false" \
  -F "image=@/path/to/image.jpg;type=image/jpeg"
```

### Успешный ответ

- Статус: `201`
- Body: `PostResponse`

### Валидации

- `text`: не пустой, максимум 5000 символов
- `image`: должен быть изображением

### Возможные ошибки

- `400`: ошибка валидации текста/файла
- `401`: нет/невалидный токен
- `404`: пользователь не найден

## 4.3 `GET /posts?limit=20&offset=0` (лента)

### Когда вызывать

- На экране ленты.
- При пагинации/дозагрузке.

### Request

Headers:

- `Authorization: Bearer <access_token>`

Query:

- `limit` (по умолчанию `20`, диапазон `1..100`)
- `offset` (по умолчанию `0`, `>= 0`)

### Успешный ответ

- Статус: `200`
- Body: массив `PostResponse[]` (может быть пустым)

### Возможные ошибки

- `400`: невалидный `limit`/`offset`
- `401`: нет/невалидный токен

## 4.4 `GET /posts/{post_id}`

### Когда вызывать

- Открытие детали поста.
- Рефреш поста после лайка/редактирования.

### Request

Headers:

- `Authorization: Bearer <access_token>`

### Успешный ответ

- Статус: `200`
- Body: `PostResponse`

### Возможные ошибки

- `400`: некорректный `post_id`
- `401`: нет/невалидный токен
- `404`: пост не найден

## 4.5 `PUT /posts/{post_id}`

### Когда вызывать

- Редактирование поста (только автор).

### Request

Headers:

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

Body:

```json
{
  "text": "Обновленный текст",
  "medias": [
    "http://localhost:9000/royality-media/post/9e8f.../f4c9.jpg"
  ],
  "disable_comments": false
}
```

Важно:

- `medias` обязателен и не может быть пустым.
- Если меняешь только текст, все равно передай текущие URL изображений.

### Успешный ответ

- Статус: `200`
- Body: обновленный `PostResponse`

### Возможные ошибки

- `400`: ошибка валидации или некорректный `post_id`
- `401`: нет/невалидный токен
- `403`: редактирует не автор
- `404`: пост/пользователь не найден

## 4.6 `DELETE /posts/{post_id}`

### Когда вызывать

- Удаление поста (только автор).

### Request

Headers:

- `Authorization: Bearer <access_token>`

### Успешный ответ

- Статус: `204`
- Тело: отсутствует

### Возможные ошибки

- `400`: некорректный `post_id`
- `401`: нет/невалидный токен
- `403`: удаляет не автор
- `404`: пост/пользователь не найден

### Как обновлять UI

- удалить пост из локальной ленты
- или перезапросить страницу ленты

## 4.7 `POST /posts/{post_id}/like`

### Когда вызывать

- Нажатие “Лайк”.

### Request

Headers:

- `Authorization: Bearer <access_token>`

Body: отсутствует

### Успешный ответ

- Статус: `204`
- Тело: отсутствует

### Возможные ошибки

- `400`: некорректный `post_id`
- `401`: нет/невалидный токен
- `404`: пост/пользователь не найден

### Обновление UI

Вариант A (оптимистично):

- `is_liked = true`
- `likes_count += 1`

Вариант B:

- после `204` вызвать `GET /posts/{post_id}`.

## 4.8 `DELETE /posts/{post_id}/like`

### Когда вызывать

- Нажатие “Убрать лайк”.

### Request

Headers:

- `Authorization: Bearer <access_token>`

Body: отсутствует

### Успешный ответ

- Статус: `204`
- Тело: отсутствует

### Возможные ошибки

- `400`: некорректный `post_id`
- `401`: нет/невалидный токен
- `404`: пост/пользователь не найден

### Обновление UI

Вариант A (оптимистично):

- `is_liked = false`
- `likes_count = max(0, likes_count - 1)`

Вариант B:

- после `204` вызвать `GET /posts/{post_id}`.

Важно по лайкам:

- После `POST /like` поле `is_liked` в последующем `GET /posts`/`GET /posts/{id}` станет `true`.
- После `DELETE /like` поле `is_liked` станет `false`.

## 5. Медиа (универсальная загрузка)

## 5.0 `POST /users/me/avatar` (рекомендуемый способ для аватара)

### Когда вызывать

- При выборе/изменении аватарки в профиле.

### Request

Headers:

- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

Form-data:

- `image` (обязательно, файл изображения)

### Успешный ответ

- Статус: `200`

```json
{
  "url": "http://localhost:9000/royality-media/profile/<user_id>/<file>.png"
}
```

### Как использовать на frontend

1. Вызвать `POST /users/me/avatar`.
2. Получить `url` из ответа.
3. Передать этот `url` в `PUT /users/me` как `avatar_url`.

### Возможные ошибки

- `400`: невалидный файл (не image/пустой)
- `401`: нет/невалидный токен

## 5.1 `POST /media/upload?tag=...`

### Когда вызывать

- Когда нужно заранее получить URL картинки (например, для аватара).

### Request

Headers:

- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

Query:

- `tag` (обязательно), пример: `profile/<user_id>`

Form-data:

- `file` (обязательно, изображение)

Пример:

```bash
curl -X POST "http://localhost:8000/api/v1/media/upload?tag=profile/9e8f3e2c-5f2a-4e4f-8f47-0a4bbef2a0bc" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/avatar.png;type=image/png"
```

### Успешный ответ

- Статус: `200`

```json
{
  "url": "http://localhost:9000/royality-media/profile/9e8f.../9c1d4f5a.png"
}
```

### Валидации

- файл не пустой
- `content-type` должен начинаться с `image/`
- `tag`:
  - не пустой
  - не начинается и не заканчивается `/`
  - не содержит `..` и `\`
  - только символы `[a-zA-Z0-9/_-]+`

### Возможные ошибки

- `400`: ошибка валидации файла/тега
- `401`: нет/невалидный токен

## 6. Как frontend работает с картинками

- Картинки постов берутся из `post.medias[]`.
- Аватар профиля берется из `profile.avatar_url`.
- Эти URL можно напрямую подставлять в `<img src="...">`.

Для локальной разработки endpoint MinIO должен быть доступен браузеру.
Обычно в `.env` используется:

- `ROYALITY_DOCKER_MINIO_PUBLIC_ENDPOINT=localhost:9000`

## 7. Полный рекомендуемый сценарий для приложения

1. Пользователь логинится через `POST /users/login`.
2. Frontend сохраняет `access_token`.
3. Frontend запрашивает `GET /users/me` и заполняет шапку/профиль.
4. Frontend запрашивает `GET /posts?limit=20&offset=0`.
5. При открытии чужого профиля делает `GET /users/{user_id}`.
6. При нажатии follow/unfollow вызывает `POST/DELETE /users/{user_id}/follow`.
7. После follow/unfollow обновляет `is_following` и `followers_count` локально или через повторный `GET`.
8. При создании поста отправляет `POST /posts` (`multipart/form-data`).
9. При лайке/анлайке вызывает `POST/DELETE /posts/{post_id}/like`.
10. После лайка/анлайка обновляет счетчик локально или перезапрашивает пост.

## 8. Таблица статусов для frontend

- `200` — успешный `GET/PUT` или `media/upload`
- `201` — успешное создание (`signup`, `post`)
- `204` — успех без тела (`follow`, `unfollow`, `like`, `unlike`, `delete`)
- `400` — ошибка валидации или некорректный UUID/параметр
- `401` — требуется авторизация или токен невалидный
- `403` — недостаточно прав (например, чужой пост edit/delete)
- `404` — сущность не найдена
- `409` — конфликт (например, логин уже занят)

## 9. Что пока не реализовано (важно для планирования UI)

- Комментарии к постам
- Отдельные ручки аналитики лайков/подписок

## 10. Короткий FAQ для frontend

### Нужно ли ждать body после лайка/подписки?

Нет. Для этих действий backend возвращает `204` без тела.

### Можно ли рендерить URL MinIO напрямую?

Да. `medias` и `avatar_url` — это готовые публичные URL.

### Почему `is_following` бывает `false` на своем профиле?

Это ожидаемое поведение: пользователь не может быть подписан сам на себя.

### Что использовать для “мой профиль”: `/users/{id}` или `/users/me`?

Для “мой профиль” использовать `GET /users/me`.
`/users/{id}` использовать для профилей по id, обычно чужих.
