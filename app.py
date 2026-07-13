from datetime import date, datetime, time, timedelta

import streamlit as st

from pawpal_system import Owner, Pet, VALID_STATUSES


PRIORITY_VALUES = {"low": 1, "medium": 2, "high": 3}
TASK_TYPES = ["feeding", "walk", "meds", "grooming", "enrichment"]
RECURRENCE_OPTIONS = ["none", "daily", "weekly"]


def get_owner():
    """Return the persisted owner for this Streamlit session."""
    if "owner" not in st.session_state:
        st.session_state["owner"] = Owner()
    return st.session_state["owner"]


def pet_rows(owner):
    """Build table rows for the owner's pets."""
    return [
        {
            "Name": pet.name,
            "Species": pet.type,
            "Weight": pet.weight,
            "Task count": len(pet.tasks),
        }
        for pet in owner.pets
    ]


def task_rows(tasks):
    """Build table rows for scheduled tasks."""
    return [
        {
            "Date": task.date,
            "Time": task.time,
            "Window": task_window(task),
            "Pet": task.pet.name,
            "Task": task.task_type.title(),
            "Duration": task.duration_minutes,
            "Priority": task.priority,
            "Status": task.status,
            "Repeats": task.recurrence,
            "Reason": task.reason,
        }
        for task in tasks
    ]


def skipped_rows(skipped_tasks):
    """Build table rows for tasks skipped by the schedule builder."""
    return [
        {
            **task_rows([task])[0],
            "Skipped because": reason,
        }
        for task, reason in skipped_tasks
    ]


def conflict_rows(conflicts):
    """Build table rows for pairs of tasks that overlap."""
    rows = []
    for first_task, second_task in conflicts:
        rows.append(
            {
                "Date": first_task.date,
                "First task": task_label(first_task),
                "First window": task_window(first_task),
                "Second task": task_label(second_task),
                "Second window": task_window(second_task),
            }
        )
    return rows


def task_label(task):
    """Create a compact label for task selection controls."""
    return f"{task.date} {task.time} - {task.pet.name} {task.task_type.title()}"


def task_window(task):
    """Create a start-end display window for a scheduled task."""
    start = datetime.strptime(task.time, "%H:%M")
    end = start + timedelta(minutes=max(task.duration_minutes, 1))
    return f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"


def time_block(task):
    """Group tasks into broad parts of the day."""
    hour = int(task.time.split(":")[0])
    if hour < 12:
        return "Morning"
    if hour < 17:
        return "Afternoon"
    return "Evening"


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

owner = get_owner()

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input(
    "Owner name",
    value=st.session_state.get("owner_name", "Jordan"),
)
st.session_state["owner_name"] = owner_name

owner.availability = int(
    st.number_input(
        "Available care time today (minutes)",
        min_value=0,
        max_value=1440,
        value=int(owner.availability or 120),
    )
)

st.subheader("Pets")
pet_col1, pet_col2, pet_col3 = st.columns(3)
with pet_col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with pet_col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with pet_col3:
    weight = st.number_input("Weight", min_value=0.1, value=22.5, step=0.5)

if st.button("Add pet"):
    try:
        clean_pet_name = pet_name.strip()
        owner.add_pet(Pet(clean_pet_name, species, float(weight)))
        st.success(f"Added {clean_pet_name} to {owner_name}'s pets.")
    except (TypeError, ValueError) as error:
        st.error(str(error))

if owner.pets:
    st.table(pet_rows(owner))
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Tasks")

if owner.pets:
    task_col1, task_col2 = st.columns(2)
    with task_col1:
        selected_pet_index = st.selectbox(
            "Pet",
            range(len(owner.pets)),
            format_func=lambda index: owner.pets[index].name,
        )
        task_type = st.selectbox("Task type", TASK_TYPES)
        task_time = st.time_input("Time", value=time(8, 0))
        task_date = st.date_input("Date", value=date.today())
    with task_col2:
        duration = st.number_input(
            "Duration (minutes)",
            min_value=1,
            max_value=240,
            value=20,
        )
        priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        recurrence = st.selectbox("Repeat", RECURRENCE_OPTIONS)
        repeat_count = st.number_input(
            "Additional repeats",
            min_value=0,
            max_value=30,
            value=0,
            disabled=recurrence == "none",
        )
        reason = st.text_input("Reason", value="")

    if st.button("Add task"):
        pet = owner.pets[selected_pet_index]
        scheduler_method = getattr(owner.scheduler, task_type)
        scheduled_task = scheduler_method(
            pet,
            task_time.strftime("%H:%M"),
            PRIORITY_VALUES[priority_label],
            duration_minutes=int(duration),
            reason=reason,
            date=task_date.isoformat(),
            recurrence=recurrence,
            repeat_count=int(repeat_count) if recurrence != "none" else 0,
        )
        candidate_tasks = owner.scheduler.create_recurring_tasks(scheduled_task)
        conflicts = []
        for candidate_task in candidate_tasks:
            for existing_task in owner.scheduler.conflicts_for_task(
                candidate_task, owner.task.view_tasks()
            ):
                conflicts.append((candidate_task, existing_task))

        for candidate_task in candidate_tasks:
            owner.add_task(candidate_task)

        if conflicts:
            st.warning("Added task, but it overlaps with existing care tasks.")
            st.table(conflict_rows(conflicts))
        else:
            st.success(f"Added {len(candidate_tasks)} {task_type} task(s) for {pet.name}.")
else:
    st.info("Add a pet before scheduling tasks.")

current_tasks = owner.scheduler.get_tasks_for_owner_pets(owner)
if current_tasks:
    st.write("Current tasks")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        pet_filter = st.selectbox(
            "Filter by pet",
            ["All pets"] + owner.pets,
            format_func=lambda option: option if isinstance(option, str) else option.name,
        )
    with filter_col2:
        status_filter = st.selectbox("Filter by status", ["all"] + sorted(VALID_STATUSES))
    with filter_col3:
        sort_filter = st.selectbox("Sort tasks", ["time", "priority", "current"])

    selected_pet = None if pet_filter == "All pets" else pet_filter
    selected_status = None if status_filter == "all" else status_filter
    selected_sort = None if sort_filter == "current" else sort_filter
    visible_tasks = owner.scheduler.get_filtered_tasks(
        owner,
        pet=selected_pet,
        status=selected_status,
        sort_by=selected_sort,
    )
    if visible_tasks:
        st.success(f"Showing {len(visible_tasks)} task(s) from the scheduler filter.")
    else:
        st.warning("No tasks match the selected pet/status filters.")

    status_tasks = owner.scheduler.get_filtered_tasks(owner, sort_by="time")
    if status_tasks:
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            selected_status_task = st.selectbox(
                "Task to update",
                status_tasks,
                format_func=task_label,
            )
        with status_col2:
            new_status = st.selectbox(
                "New status",
                ["pending", "complete", "skipped"],
                index=["pending", "complete", "skipped"].index(
                    selected_status_task.status
                ),
            )
        if st.button("Update task status"):
            if new_status == "complete":
                selected_status_task.mark_complete()
            elif new_status == "skipped":
                selected_status_task.mark_skipped()
            else:
                selected_status_task.status = "pending"
            st.success(f"Updated {task_label(selected_status_task)}.")

    st.write("Scheduler views")
    task_tab, priority_tab, time_tab, conflict_tab = st.tabs(
        ["Filtered", "Priority order", "Time order", "Conflicts"]
    )
    with task_tab:
        if visible_tasks:
            st.table(task_rows(visible_tasks))
        else:
            st.warning("No filtered tasks to display.")
    with priority_tab:
        priority_tasks = owner.scheduler.get_filtered_tasks(owner, sort_by="priority")
        st.success("Priority order uses Scheduler.get_filtered_tasks(sort_by='priority').")
        st.table(task_rows(priority_tasks))
    with time_tab:
        chronological_tasks = owner.scheduler.get_filtered_tasks(owner, sort_by="time")
        st.success("Time order uses Scheduler.get_filtered_tasks(sort_by='time').")
        st.table(task_rows(chronological_tasks))
    with conflict_tab:
        all_conflicts = owner.scheduler.find_conflicts(current_tasks)
        if all_conflicts:
            st.warning(f"Found {len(all_conflicts)} scheduling conflict(s).")
            st.table(conflict_rows(all_conflicts))
        else:
            st.success("No overlapping pending tasks were found.")

st.divider()

st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    schedule, skipped = owner.scheduler.build_daily_plan_details(
        owner, owner.availability
    )
    st.session_state["schedule"] = schedule
    st.session_state["skipped"] = skipped

schedule = st.session_state.get("schedule", [])
skipped = st.session_state.get("skipped", [])
if schedule:
    st.success(f"Generated {len(schedule)} scheduled task(s) within the time budget.")
    schedule_view = st.selectbox("Schedule view", ["Table", "By pet", "By time block"])
    if schedule_view == "Table":
        st.table(task_rows(schedule))
    elif schedule_view == "By pet":
        for pet in owner.pets:
            pet_tasks = [task for task in schedule if task.pet == pet]
            if pet_tasks:
                st.write(pet.name)
                st.table(task_rows(pet_tasks))
    else:
        for block in ["Morning", "Afternoon", "Evening"]:
            block_tasks = [task for task in schedule if time_block(task) == block]
            if block_tasks:
                st.write(block)
                st.table(task_rows(block_tasks))

    if skipped:
        st.warning("Some pending tasks did not fit within the available care time.")
        st.table(skipped_rows(skipped))
    else:
        st.success("All pending tasks fit within the available care time.")
else:
    st.info("No generated schedule yet.")
