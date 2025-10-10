from django.shortcuts import render, redirect, HttpResponseRedirect, reverse, HttpResponse
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.generic.edit import CreateView, View, FormView
from .models import CustomUserUser as User
from .forms import SignUpForm, SignInForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from flights.models import Booking
import pyotp
import qrcode
import io
import base64

# Create your views here.


def verify_2fa_otp(user, otp):
    totp = pyotp.TOTP(user.mfa_secret)
    if totp.verify(otp):
        user.mfa_enaabled = True
        user.save()
        return True
    return False

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
        # Автоматически авторизуем пользователя после регистрации
        username = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            messages.error(self.request, 'Аккаунт с таким email уже существует.')
            return super().form_invalid(form)
            #return response#HttpResponseRedirect(reverse('user_management:signup'))
        else:
            user = User.objects.create_user(username=username, email=username, password=password)
            user.save()
            login(self.request, user)
            messages.success(self.request, f'Добро пожаловать!')
            return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class SignInView(FormView):
    template_name = 'user_management/auth.html'
    form_class = SignInForm
    success_url = reverse_lazy('flights:home')
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Вы уже вошли в систему.')
            return redirect('flights:home')
        else:
            return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        username = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Добро пожаловать!')
            return super().form_valid(form)
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
    orders = Booking.objects.filter(user=request.user).order_by('-created_at')[:10]
    print(orders)
    context = {
        'user': request.user,
        'orders': orders
    }
    return render(request, 'user_management/profile.html', context)


@login_required
def qrCodePage(request):
    user = request.user
    if not user.mfa_secret:
        user.mfa_secret = pyotp.random_base32()
        user.save()
    otp_uri = pyotp.totp.TOTP(user.mfa_secret).provisioning_uri(
        name=user.email,
        issuer_name='NESZEN'
    )

    qr = qrcode.make(otp_uri)
    buffer = io.BytesIO
    qr.save(buffer, format="PNG")

    buffer.seek(0)
    qr_code = base64.b64encode(buffer.getvalue()).decode('utf-8')

    qr_code_data_uri = f"data:image/png;base64,{qr_code}"

    return render(request, 'user_menegment/qrCodePage.html')


def verify_mfa(request):
    if request.method == 'POST':
        otp = request.POST.get('otp_code')
        user_id = request.POST.get('user_id')
        if not user_id:
            messages.error(request, 'Неверный id пользователя')
            return render(request, 'otp_verify.html', {'user_id': user_id})
        user = User.objects.get(id=user_id)
        if verify_2fa_otp(user, otp):
            if request.user.is_authenticated:
                messages.success(request, '2FA enabled successfully !')
                return redirect('user_managment:qrCodePage')
            login(request, user)
            messages.success(request, 'Вы вошли!')
            return redirect('user_managment:qrCodePage')
        else:
            messages.error(request, 'Неверный код')
            if request.user.is_authenticated:
                return redirect('user_managment:qrCodePage')
            return render(request, 'otp_verify.html', {'user_id': user_id})
            
    return render(request, 'otp_verify.html', {'user_id': user_id})
