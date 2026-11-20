def preparation_notice(task, coursework):
    if not task.get("preparation") or not coursework:
        return None
    start, end = task.get("start_time", ""), task.get("end_time", "")
    if len(end) != 16:
        return None
    title = coursework["item_name"]
    cutoff = coursework.get("cutoff")
    timing = f"“{task['name']}” ({start.replace('T', ' ')} to {end.replace('T', ' ')})"
    if cutoff and end > cutoff:
        return "late", f"{timing} prepares for “{title}”. Finish by {cutoff.replace('T', ' ')}."
    if not cutoff:
        due = coursework["due_date"]
        if end[:10] > due:
            return "late", f"{timing} prepares for “{title}”. Finish on or before {due}; the exact cutoff is unknown."
        if end[:10] == due:
            return "unknown", f"“{task['name']}” ends on the due date for “{title}”. The exact cutoff is unknown; enter it in Coursework to check this time."
    return None


def validate_preparation(task, coursework):
    notice = preparation_notice(task, coursework)
    if notice and notice[0] == "late":
        raise ValueError(notice[1] + " Saved times were not changed.")
