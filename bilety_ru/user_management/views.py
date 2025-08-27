from django.shortcuts import render, redirect, HttpResponseRedirect, reverse, HttpResponse
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.generic.edit import CreateView, View, FormView
from django.contrib.auth.models import User
from .forms import SignUpForm, SignInForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

# Create your views here.


class SignUpView(CreateView):
    template_name = 'user_management/signup.html'
    form_class = SignUpForm
    success_url = reverse_lazy('flights:home')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('flights:home'))
        else:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        # Автоматически авторизуем пользователя после регистрации
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Добро пожаловать, {user.first_name}! Вы успешно зарегистрированы.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class SignInView(FormView):
    template_name = 'user_management/auth.html'
    form_class = SignInForm
    success_url = reverse_lazy('flights:home')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('flights:home')
        else:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Добро пожаловать, {user.first_name}!')
            # Перенаправляем на страницу, с которой пользователь пришел, если есть
            next_page = self.request.GET.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'Неверное имя пользователя или пароль.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Неверное имя пользователя или пароль.')
        return super().form_invalid(form)


class LogOutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'Вы успешно вышли из системы.')
        return redirect('flights:home')


@login_required
def profile(request):
    """Страница профиля пользователя"""
    from flights.models import FlightRequest
    
    # Получаем историю поисков пользователя
    flight_requests = FlightRequest.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'user': request.user,
        'flight_requests': flight_requests
    }
    
    return render(request, 'user_management/profile.html', context)


def index(request):
    """Главная страница управления пользователями"""
    if request.user.is_authenticated:
        return redirect('user_management:profile')
    return redirect('user_management:signin')
