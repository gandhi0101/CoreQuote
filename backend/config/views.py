from django.shortcuts import render


def home(request):
    """Landing page for CoreQuote."""

    return render(request, "home.html")
