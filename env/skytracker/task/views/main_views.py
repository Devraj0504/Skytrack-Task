from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import check_password, make_password
from task.models import Master_Project, Master_Task, Master_User
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
from django.views.decorators.http import require_http_methods
import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def dashboard_view(request):
    user = request.user.master_user

    if user.user_type == 1:
        total_projects = Master_Project.objects.count()
        total_tasks = Master_Task.objects.count()
        task_counts_by_status_qs = (
            Master_Task.objects.values("status").annotate(count=Count("task_id"))
        )
        today = timezone.now().date()
        upcoming_tasks = (
            Master_Task.objects.filter(
                status__in=["todo", "in_progress"],
                due_date__isnull=False,
                due_date__gte=today,
            )
            .order_by("due_date", "priority")[:5]
        )
    else:
        total_projects = Master_Project.objects.filter(owner=user).count()
        total_tasks = Master_Task.objects.filter(project__owner=user).count()
        task_counts_by_status_qs = (
            Master_Task.objects.filter(project__owner=user)
            .values("status")
            .annotate(count=Count("task_id"))
        )
        today = timezone.now().date()
        upcoming_tasks = (
            Master_Task.objects.filter(
                project__owner=user,
                status__in=["todo", "in_progress"],
                due_date__isnull=False,
                due_date__gte=today,
            )
            .order_by("due_date", "priority")[:5]
        )

    task_counts_by_status = {row["status"]: row["count"] for row in task_counts_by_status_qs}

    if not upcoming_tasks:
        upcoming_tasks = "No upcoming tasks!"

    context = {
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "task_counts_by_status": task_counts_by_status,
        "upcoming_tasks": upcoming_tasks,
    }
    return render(request, "accounts/dashboard.html", context)

@csrf_exempt
def create_project(request):
    user = request.user.master_user
    if request.POST:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST

        name = data.get("name")
        description = data.get("description", "")

        if not name:
            return JsonResponse({"error": "Project name is required"}, status=400)

        project = Master_Project.objects.create(name=name, description=description, owner=user)

        return JsonResponse(
            {
                "project_id": project.project_id,
                "name": project.name,
                "description": project.description,
                "owner": project.owner.user_name,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            },
            status=201,
        )
    else:
        user_list = Master_User.objects.filter(status=1)
        return render(request, "project/project_create.html", {"user_list": user_list})

@csrf_exempt
@login_required
def projects_view(request):
    user = request.user.master_user

    if request.method == "POST":
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
        name = data.get("name")
        description = data.get("description", "")
        manager_id = data.get("project_manager")
        manager = Master_User.objects.get(u_id=manager_id)

        if not name:
            return JsonResponse({"error": "Project name is required"}, status=400)

        owner_to_check = manager if user.user_type == 1 else user

        if Master_Project.objects.filter(owner=owner_to_check, name=name).exists():
            return JsonResponse({"error": "Project with this name already exists"}, status=400)

        project = Master_Project.objects.create(
            name=name,
            description=description,
            owner=manager
        )

        return JsonResponse(
            {
                "project_id": project.project_id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "owner": project.owner.user_name,
            },
            status=201
        )

    if user.user_type == 1:
        projects = Master_Project.objects.all()
    else:
        projects = Master_Project.objects.filter(
            Q(owner=user) | Q(tasks__assignee=user)
        ).distinct()

    projects_data = [
        {
            "project_id": p.project_id,
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "owner": p.owner.user_name,
        }
        for p in projects
    ]

    return JsonResponse({"projects": projects_data})



@csrf_exempt
@login_required
def project_spreadsheet(request):
    project_id = request.POST.get("project_id") or request.GET.get("project_id")
    if not project_id:
        return HttpResponse("Missing project_id parameter.", status=400)

    user = request.user.master_user

    if user.user_type == 1:
        project = get_object_or_404(Master_Project, project_id=project_id)
    else:
        project = get_object_or_404(Master_Project, project_id=project_id, owner=user)

    user_list = Master_User.objects.filter(status=1)
    return render(request, "project/task.html", {
        "project": project,
        "project_id": project.project_id,
        "project_name": project.name,
        "user_list": user_list,
    })
    
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def project_tasks_view(request, project_id):
    user = request.user.master_user

    # Check project access
    if user.user_type == 1:
        project = get_object_or_404(Master_Project, project_id=project_id)
    else:
        project = get_object_or_404(Master_Project, project_id=project_id, owner=user)

    # Parse data
    data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    title = data.get("title")
    description = data.get("description", "")
    status = data.get("status", "todo")
    priority = data.get("priority")
    assignee_id = data.get("assignee_id")
    due_date_str = data.get("due_date")
    due_date = None

    # Required fields
    if not title or not priority:
        return JsonResponse({"error": "Title and priority are required."}, status=400)

    # Priority check
    try:
        priority = int(priority)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Priority must be an integer."}, status=400)

    # Due date validation
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid due_date format, must be YYYY-MM-DD."}, status=400)

    # Assignee check
    assignee = None
    if assignee_id:
        try:
            assignee = Master_User.objects.get(u_id=assignee_id)
        except Master_User.DoesNotExist:
            return JsonResponse({"error": "Assignee not found."}, status=400)

    # Permission check
    if not (user.user_type == 1 or project.owner == user):
        return JsonResponse({"error": "You do not have permission to add tasks to this project."}, status=403)

    # Create task
    task = Master_Task(
        project=project,
        title=title,
        description=description,
        status=status,
        priority=priority,
        due_date=due_date,
        assignee=assignee,
    )

    # Model-level validation (priority range, done+future-date)
    try:
        task.save()
    except ValidationError as e:
        messages = e.message_dict if hasattr(e, "message_dict") else e.messages
        return JsonResponse({"error": messages}, status=400)

    return JsonResponse(
        {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else "",
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "assignee": task.assignee.user_name if task.assignee else None,
        },
        status=201,
    )
@login_required
def tasks_list(request):
    user = request.user.master_user

    if getattr(user, "user_type", None) == 1:
        qs = Master_Task.objects.select_related("project", "assignee").all()
    else:
        base_q = Q(project__owner=user) | Q(assignee=user)

        creator_field = None
        for name in ("created_by", "created_user", "creator", "added_by", "created_by_id"):
            try:
                Master_Task._meta.get_field(name)
                creator_field = name
                break
            except Exception:
                continue

        if creator_field:
            if creator_field.endswith("_id"):
                if hasattr(user, "u_id"):
                    base_q |= Q(**{creator_field: user.u_id})
            else:
                base_q |= Q(**{creator_field: user})

        qs = Master_Task.objects.select_related("project", "assignee").filter(base_q)

    status = request.GET.get("status")
    project_id = request.GET.get("project_id")
    due_before = request.GET.get("due_before")

    if status:
        qs = qs.filter(status=status)

    if project_id:
        qs = qs.filter(project__project_id=project_id)

    if due_before:
        try:
            due_date = datetime.strptime(due_before, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid due_before format, must be YYYY-MM-DD."}, status=400)
        qs = qs.filter(due_date__lte=due_date)

    qs = qs.order_by("due_date", "priority")

    tasks = [
        {
            "task_id": t.task_id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else "",
            "project_id": t.project.project_id,
            "project_name": t.project.name,
            "assignee_id": t.assignee.u_id if t.assignee else None,
            "assignee": t.assignee.user_name if t.assignee else None,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in qs
    ]

    return JsonResponse({"tasks": tasks})
