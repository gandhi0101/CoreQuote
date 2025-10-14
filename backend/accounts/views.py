from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CompanyProfileForm
from .models import CompanyProfile


@login_required
def profile(request):
    """Display and edit the user's company profile."""

    profile, _ = CompanyProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = CompanyProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos fiscales actualizados correctamente.")
            return redirect("accounts:profile")
    else:
        form = CompanyProfileForm(instance=profile)

    return render(request, "accounts/profile.html", {"form": form, "profile": profile})
