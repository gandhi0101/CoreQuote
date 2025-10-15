from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CompanyProfileForm, StyledPasswordChangeForm, UserAccountForm
from .models import CompanyProfile


@login_required
def profile(request):
    """Display and edit the user's company profile."""

    profile, _ = CompanyProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        if request.POST.get("action") == "update-account":
            account_form = UserAccountForm(request.POST, instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user)
            profile_form = CompanyProfileForm(instance=profile)

            if account_form.is_valid():
                account_form.save()
                messages.success(request, "Información de cuenta actualizada correctamente.")
                return redirect("accounts:profile")
        elif request.POST.get("action") == "change-password":
            account_form = UserAccountForm(instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            profile_form = CompanyProfileForm(instance=profile)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Contraseña actualizada correctamente.")
                return redirect("accounts:profile")
        else:
            account_form = UserAccountForm(instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user)
            profile_form = CompanyProfileForm(request.POST, request.FILES, instance=profile)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Datos fiscales actualizados correctamente.")
                return redirect("accounts:profile")
    else:
        account_form = UserAccountForm(instance=request.user)
        password_form = StyledPasswordChangeForm(user=request.user)
        profile_form = CompanyProfileForm(instance=profile)

    return render(
        request,
        "accounts/profile.html",
        {
            "account_form": account_form,
            "password_form": password_form,
            "profile_form": profile_form,
            "profile": profile,
        },
    )
