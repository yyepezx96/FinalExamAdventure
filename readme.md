# 👤 Final Exam Adventure – User Profile Management Feature

## 🚀 Feature Implemented: User Profile Management

This project enhances the User Management System by implementing the **User Profile Management** feature. Users can now update their professional profiles, and admins/managers can upgrade users to professional status with notification support.

### 🛠️ Core Functionality

- Users can update profile fields: `bio`, `linkedin_profile_url`, `github_profile_url`, and more
- Admins/Managers can upgrade users to `professional` status
- Users receive notification emails upon status upgrade
- Validations added for URL fields and update rules

---

## 🐞 5 Quality Assurance (QA) Issues Addressed

| # | Issue Title | Summary |
|--|-------------|---------|
| 1 | [Username Validation Bug](https://github.com/yyepezx96/FinalExamAdventure/issues/1) | Enforced nickname pattern to allow only alphanumeric, hyphen, or underscore |
| 2 | [Password Strength](https://github.com/yyepezx96/FinalExamAdventure/issues/2) | Added password policy requiring complexity and minimum length |
| 3 | [Profile Update Edge Cases](https://github.com/yyepezx96/FinalExamAdventure/issues/3) | Fixed handling of optional profile fields (like `bio`, `LinkedIn`, `GitHub`) |
| 4 | [Upgrade to Professional](https://github.com/yyepezx96/FinalExamAdventure/issues/4) | Fixed route for managers/admins to upgrade users and send email |
| 5 | [Missing Validation on Profile Update](https://github.com/yyepezx96/FinalExamAdventure/issues/5) | Prevented updates to forbidden fields like `role`, `is_locked`, etc. |

🔗 **Closed Issues:** [See GitHub Issues »](https://github.com/yyepezx96/FinalExamAdventure/issues?q=is%3Aissue+is%3Aclosed)

---

## ✅ 10 New Tests Added

| # | Test Description |
|--|------------------|
| 1 | Validates user bio update via PUT endpoint |
| 2 | Validates LinkedIn URL update with proper formatting |
| 3 | Validates GitHub URL update with proper formatting |
| 4 | Rejects profile update if no fields are provided |
| 5 | Rejects invalid URL formats (e.g., not HTTPS) |
| 6 | Prevents update of restricted fields like `role`, `is_locked` |
| 7 | Confirms upgrade endpoint sets `is_professional = True` |
| 8 | Sends upgrade notification email successfully |
| 9 | Admin can fetch user info via `/users/{user_id}` |
| 10 | Manager role has access to upgrade endpoint |

✅ All **tests passed** (including existing + new).

---

## 🐳 DockerHub Deployment

The app was successfully built and pushed to DockerHub.

🔗 **DockerHub Image:**  
👉 [https://hub.docker.com/r/yarlina/finalexamadventure](https://hub.docker.com/r/yarlina/finalexamadventure)

```bash
docker pull yarlina/finalexamadventure:latest
```

---

## 🔁 GitHub Actions Status

GitHub Actions CI passes on all pushes to `main` and feature branches. All automated tests run in Docker and are verified against the live PostgreSQL service.

---

## 💭 Reflection

This project helped me solidify key development practices like:

- Working in isolated feature branches with pull requests
- Documenting issues and debugging with test-driven development
- Writing API tests for edge cases and backend rules
- Dockerizing the app and understanding deployment pipelines
- Finding bugs, reading codes, debugging bugs

It also strengthened my confidence in managing test fixtures, schemas, and async database interactions using FastAPI and SQLAlchemy. Coding feels like learning a new language and I feel I went from 0 knowledge to "read & write" profficiency.

---

## 📂 How to Run

```bash
# Build and start containers
docker-compose up --build

# Run tests inside the container
docker-compose exec web pytest -v
```

---

📅 Submitted: May 2025  
👩‍💻 Author: Yarlina  
🎓 Course: User Management Systems – Final Project  

