# TODO

## Backend

- [ ] **Telegram validator error handling**: The `validate_telegram_channel()` function in `backend/app/validators/telegram.py` doesn't return proper error responses - exceptions are not being caught correctly, resulting in 500 errors instead of proper validation error messages.

