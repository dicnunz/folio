from datetime import date

from django.shortcuts import redirect, render


def index(request):
    assignments = request.session.get("assignments", [])
    error = None

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        due_date = request.POST.get("due_date", date.today().isoformat())
        priority = request.POST.get("priority", "Low")

        if not name:
            error = "Assignment name is required."
        else:
            request.session["assignments"] = assignments + [
                {
                    "name": name,
                    "due_date": due_date,
                    "priority": priority,
                }
            ]
            return redirect("index")

    return render(
        request,
        "index.html",
        {
            "assignments": assignments,
            "error": error,
            "today": date.today().isoformat(),
        },
    )
