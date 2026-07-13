# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

Run with coverage:

```bash
pytest --cov
```

## Testing PawPal ++

The tests cover the most important PawPal+ scheduling behaviors:

- Sorting correctness: verifies chronological ordering by date, time, pet name, and task type so tied tasks appear in a predictable order.
- Recurrence logic: verifies daily and weekly recurring tasks expand into the expected future dates and generated follow-up tasks do not accidentally keep recurring forever.
- Conflict detection: verifies overlapping pending tasks are reported, while completed tasks, tasks on different dates, and back-to-back tasks are ignored.
- Availability planning: verifies high-priority care tasks are selected first and tasks that do not fit in the owner's available care time are reported as skipped.
- Ownership rules: verifies owners only schedule tasks for pets they own.

Successful output from `python -m pytest`:

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/sebastianbejaoui/Desktop/Software projects/AI 101/ai110-module2show-pawpal-starter
plugins: anyio-4.10.0
collected 15 items

test_paypal.py ..                                                        [ 13%]
tests/test_pawpal_system.py .............                                [100%]

============================== 15 passed in 0.02s ==============================
```

## 📐 Smarter Scheduling

PawPal+ now includes scheduling logic that goes beyond simply storing tasks. The core algorithms live in `pawpal_system.py`, and the Streamlit UI in `app.py` exposes them through task controls, filters, warnings, and schedule views.

| Feature | Method(s) | What it does |
|---------|-----------|--------------|
| Priority-based schedule sorting | `Task.sort_tasks()`, `Scheduler.build_daily_plan()`, `_priority_sort_key()` | Orders pending tasks by effective priority, then date, time, pet name, and task type for stable results. |
| Medication priority boost | `_effective_priority()` | Gives medication tasks an internal priority boost so they are less likely to be skipped when available care time is limited. |
| Chronological sorting | `Task.sort_tasks_by_time()`, `_chronological_sort_key()` | Sorts tasks by date and time without considering priority, useful for viewing the day in order. |
| Filter by pet and status | `Task.filter_tasks()`, `Scheduler.get_filtered_tasks()` | Returns only tasks for a selected pet and/or status such as `pending`, `complete`, or `skipped`. |
| Task status updates | `ScheduledTask.mark_complete()`, `ScheduledTask.mark_skipped()` | Tracks whether a care task is still pending, completed, or intentionally skipped. |
| Recurring tasks | `Scheduler.create_recurring_tasks()`, `Owner.add_task_series()` | Expands a task into additional daily or weekly due dates. Daily recurrence uses `date.today() + timedelta(days=1)` for the next due date. |
| Conflict detection | `Scheduler.find_conflicts()`, `Scheduler.conflicts_for_task()` | Detects overlapping pending tasks on the same date using each task's start time and duration. |
| Availability-aware planning | `Scheduler.build_daily_plan()`, `Owner.view_schedule()` | Builds a plan that fits inside the owner's available care minutes. |
| Skipped-task reporting | `Scheduler.build_daily_plan_details()`, `Owner.view_schedule_details()` | Returns both the selected plan and tasks skipped because they did not fit within the available time. |
| Owner/pet task ownership | `Scheduler.get_tasks_for_owner_pets()`, `Owner.add_task()` | Keeps generated schedules limited to tasks for pets owned by the current owner. |

The app uses these methods to show current task filters, warn about conflicts before and after adding tasks, generate recurring task instances, and display the final schedule as a table, by pet, or by time block.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
