# Mini Project & Task Tracker (Django)

I built this small Django app to keep track of projects and tasks across users — nothing fancy, just practical.

## What it does
- Create projects (each user keeps their own project names)
- Add tasks to a project with title, priority (1-5), status, due date and optional assignee
- Filter tasks, search projects, and view a simple dashboard
- Uses Django's session login so you can sign in and try things in the browser

## Quick notes about the rules I followed
- Project names are unique per owner (you can't create two projects with the same name under the same user).
- Task priority: 1 is highest, 5 is lowest. If you try to send a number outside 1–5 the app returns:
  **"Priority must be between 1 (highest) and 5 (lowest)."**
- If a task is marked `done`, its due date cannot be in the future. This validation runs at the model level.

## How I modeled things (short)
- **Project**: name, description, owner (User), created_at, updated_at. Unique per owner.
- **Task**: project (FK), title, description, status, priority, due_date, assignee (User), timestamps.
Model-level `clean()` is used for the priority and done/due_date checks.

## Endpoints you'll use
- `POST /projects/` — create a project (owner is the logged-in user)
- `GET  /projects/` — list projects you own; add `?search=...` to filter by name
- `POST /projects/<project_id>/tasks/` — create a task (only project owner can do this)
- `GET  /tasks/` — list tasks that belong to your projects or that are assigned to you (supports `status`, `project_id`, `due_before`)
- `GET  /dashboard/` — quick summary (counts + top 5 upcoming tasks)

## Dashboard details
The dashboard returns:
- total projects you own
- total tasks in those projects
- number of tasks by status (`todo`, `in_progress`, `done`)
- top 5 upcoming tasks (soonest due_date, ignore tasks with `status == done`)

If there are no upcoming tasks it will return the string:
**"No upcoming tasks!"**

Important: I used Django ORM aggregation and annotations for this — not manual loops.
**NOTE: I have implemented the dashboard using ORM aggregation, not manual Python loops.**

Also, you'll find this comment above the dashboard view in the code:
```
# summary-view-anchor
```

## Tests included
I added a few tests using Django's `TestCase`:
1. Can't create two projects with same name under the same user.
2. Can't set a task to `done` if its due date is in the future.
3. `/tasks/` returns only tasks in the user's own projects or where the user is the assignee.

## Run it locally (fast)
1. Create a virtualenv and install dependencies:
```
pip install -r requirements.txt
```
2. Apply migrations:
```
python manage.py makemigrations
python manage.py migrate
```
3. Create a user to log in with:
```
python manage.py createsuperuser
```
4. Start the server:
```
python manage.py runserver
```
5. Open the site and login:
```
http://127.0.0.1:8000/
```

## Notes for reviewers
- Nothing magical here — plain Django ORM, simple templates and a bit of jQuery for AJAX in the front end.
- Permissions are enforced in views: only project owners can create tasks for that project; task listing is limited to the user's projects and assigned tasks.

## Deliverables in the repo
- Django project code
- Tests in `task/tests.py`


