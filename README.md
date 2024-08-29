# ToDo list API

ToDo list API with authentication, built with FastAPI
DataBase: PosgreSQL

### Endpoints:
| **Method** | **URL** | **DESCRIPTION**     | 
|------------|---------|---------------------|
| POST       | /auth/  | register new user   |
| POST       | /token/ | create access token |
| POST       | /todo/  | create new task     |
| GET        | /todo/  | view created tasks  |
| PUT        | /todo/{task_id}  | edit tasks  |
| DELETE        | /todo/{task_id}  | delete task  |
