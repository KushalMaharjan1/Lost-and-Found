import csv
import json
import os
import time
from functools import wraps

from django.conf import settings
from django.core import signing
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.http import url_has_allowed_host_and_scheme

ADMIN_COOKIE = "lost_found_admin"


def is_admin(request):
    try:
        return signing.loads(
            request.COOKIES.get(ADMIN_COOKIE, ""),
            salt="lost-found-admin",
            max_age=settings.ADMIN_SESSION_AGE,
        ) == settings.ADMIN_USERNAME
    except signing.BadSignature:
        return False


def admin_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not is_admin(request):
            login_url = f"{reverse('login')}?next={request.get_full_path()}"
            return redirect(login_url)
        return view(request, *args, **kwargs)

    return wrapped

CSV_FILE = "data/lost_found.csv"
JSON_FILE = "data/lost_found.json"

FIELDNAMES = ["title", "status", "category", "location", "date", "description", "contact", "image"]


def login_view(request):
    if is_admin(request):
        return redirect("home")

    next_url = request.POST.get("next") or request.GET.get("next") or reverse("home")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse("home")

    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        if constant_time_compare(username, settings.ADMIN_USERNAME) and constant_time_compare(password, settings.ADMIN_PASSWORD):
            response = redirect(next_url)
            signed_user = signing.dumps(settings.ADMIN_USERNAME, salt="lost-found-admin")
            response.set_cookie(ADMIN_COOKIE, signed_user, max_age=settings.ADMIN_SESSION_AGE, httponly=True, samesite="Lax")
            return response
        error = "Invalid username or password."

    return render(request, "pages/login.html", {"error": error, "next": next_url})


def logout_view(request):
    response = redirect("home")
    response.delete_cookie(ADMIN_COOKIE)
    return response


def read_items():
    items = []
    try:
        with open(CSV_FILE, "r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                items.append(row)
    except FileNotFoundError:
        print("No records file yet.")
    return items


def write_items(items):
    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES, restval="")
        writer.writeheader()
        for item in items:
            writer.writerow(item)


def sync_json(items):
    with open(JSON_FILE, "w") as file:
        json.dump(items, file, indent=4)


def read_json():
    items = []
    try:
        with open(JSON_FILE, "r") as file:
            items = json.load(file)
    except FileNotFoundError:
        print("No JSON records file yet.")
    return items


def save_uploaded_image(uploaded_file):
    """
    Save an uploaded photo to data/images using plain file writing —
    the same open()/write() pattern used for the CSV and JSON files,
    just in binary mode for image bytes. Returns the filename that was
    saved, so it can be stored alongside the rest of the item's fields.
    """
    if not uploaded_file:
        return ""

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    # keep only the file's own name (no folders) and prefix it with a
    # timestamp so two people uploading "photo.jpg" don't overwrite
    # each other.
    safe_name = os.path.basename(uploaded_file.name)
    filename = f"{int(time.time() * 1000)}_{safe_name}"
    destination_path = os.path.join(settings.MEDIA_ROOT, filename)

    with open(destination_path, "wb") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return filename


def delete_image_file(filename):
    if not filename:
        return
    path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(path):
        os.remove(path)


def home(request):
    items = read_items()

    total = len(items)
    lost = 0
    found = 0
    resolved = 0

    for item in items:
        if item["status"] == "LOST":
            lost = lost + 1
        elif item["status"] == "FOUND":
            found = found + 1
        elif item["status"] == "RESOLVED":
            resolved = resolved + 1

    context = {
        "total": total,
        "lost": lost,
        "found": found,
        "resolved": resolved,
        "recent_items": items,
    }

    return render(request, "pages/home.html", context)


def items(request):
    all_items = read_items()

    # simple search/filter using GET params
    query = request.GET.get("q", "").strip().lower()
    status_filter = request.GET.get("status", "").strip()

    if query:
        all_items = [
            item for item in all_items
            if query in item["title"].lower() or query in item["location"].lower()
        ]

    if status_filter:
        all_items = [item for item in all_items if item["status"] == status_filter]

    context = {
        "items": list(enumerate(all_items)),
        "query": query,
        "status_filter": status_filter,
    }

    return render(request, "pages/items.html", context)


def report(request):
    if request.method == "POST":
        image_filename = save_uploaded_image(request.FILES.get("image"))

        new_item = {
            "title": request.POST.get("title", "").strip(),
            "status": request.POST.get("status", "LOST") if request.POST.get("status") in {"LOST", "FOUND"} else "LOST",
            "category": request.POST.get("category", "").strip(),
            "location": request.POST.get("location", "").strip(),
            "date": request.POST.get("date", "").strip(),
            "description": request.POST.get("description", "").strip(),
            "contact": request.POST.get("contact", "").strip(),
            "image": image_filename,
        }

        all_items = read_items()
        all_items.append(new_item)
        write_items(all_items)
        sync_json(all_items)

        return redirect("items")

    return render(request, "pages/report.html")


def detail(request, item_id):
    all_items = read_items()

    item = None
    if 0 <= item_id < len(all_items):
        item = all_items[item_id]

    context = {
        "item": item,
        "item_id": item_id,
    }

    return render(request, "pages/detail.html", context)


@admin_required
def delete_item(request, item_id):
    if request.method == "POST":
        all_items = read_items()
        if 0 <= item_id < len(all_items):
            delete_image_file(all_items[item_id].get("image"))
            all_items.pop(item_id)
            write_items(all_items)
            sync_json(all_items)

    return redirect("items")


@admin_required
def edit_item(request, item_id):
    all_items = read_items()

    if not (0 <= item_id < len(all_items)):
        return redirect("items")

    if request.method == "POST":
        existing_image = all_items[item_id].get("image", "")

        # only replace the photo if a new one was actually chosen
        uploaded = request.FILES.get("image")
        if uploaded:
            delete_image_file(existing_image)
            image_filename = save_uploaded_image(uploaded)
        else:
            image_filename = existing_image

        updated_item = {
            "title": request.POST.get("title", "").strip(),
            "status": request.POST.get("status", "LOST"),
            "category": request.POST.get("category", "").strip(),
            "location": request.POST.get("location", "").strip(),
            "date": request.POST.get("date", "").strip(),
            "description": request.POST.get("description", "").strip(),
            "contact": request.POST.get("contact", "").strip(),
            "image": image_filename,
        }

        all_items[item_id] = updated_item
        write_items(all_items)
        sync_json(all_items)

        return redirect("detail", item_id=item_id)

    context = {
        "item": all_items[item_id],
        "item_id": item_id,
    }

    return render(request, "pages/edit.html", context)
