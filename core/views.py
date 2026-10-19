from django.contrib.staticfiles import finders
from django.http import FileResponse, Http404
from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def favicon(request):
    """Serve the SVG favicon at /favicon.ico so browsers that ask for it get an answer, not a 404."""
    path = finders.find("img/favicon.svg")
    if path is None:
        raise Http404("favicon not found")
    return FileResponse(
        open(path, "rb"),
        content_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )
