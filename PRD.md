# PRD.md — Facebook OAuth Fix
## Goal
Fix and harden the Facebook OAuth login in the backend so it is production-ready.

## Tasks
- [x] Task 1: Add FACEBOOK_APP_ID and FACEBOOK_APP_SECRET to .env.example and auth.py config
- [x] Task 2: Harden verify_facebook_token() — validate token via /debug_token API before accepting
- [x] Task 3: Add facebook_id and auth_provider fields to User model in models.py
- [x] Task 4: Fix get_or_create_facebook_user() — lookup by facebook_id first, prevent duplicates, save profile_photo
- [x] Task 5: Update Facebook Graph API fields to include picture.type(large)
- [x] Task 6: Create tests/test_facebook_auth.py with 4 unit tests
