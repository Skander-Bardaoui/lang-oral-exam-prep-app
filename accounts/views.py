from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegisterForm

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('setup')

    next_url = request.POST.get('next') or request.GET.get('next') or ''
    error = request.GET.get('error')
    registered = request.GET.get('registered') == 'true'

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            if user is None:
                error = 'E-mail ou mot de passe incorrect'
            else:
                login(request, user)
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect('setup')
    else:
        form = LoginForm()

    return render(
        request,
        'auth/login.html',
        {
            'form': form,
            'error': error,
            'registered': registered,
            'next': next_url,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('setup')

    error = request.GET.get('error')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data['password'],
            )
            return redirect(f"{reverse('login')}?registered=true")
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form, 'error': error})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def account_view(request):
    return render(
        request,
        'account.html',
        {
            'recent_sessions': request.user.exam_sessions.all()[:5],
        },
    )
