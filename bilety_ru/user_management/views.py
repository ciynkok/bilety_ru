from django.shortcuts import render, redirect, HttpResponseRedirect, reverse, HttpResponse
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.generic.edit import CreateView, View, FormView
from .models import CustomUser as User
from .forms import SignUpForm, SignInForm, EmailAuthenticationForm, CustomUserCreationForm
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
        user.mfa_enabled = True
        user.save()
        return True
    return False

class SignUpView(CreateView):
    template_name = 'user_management/signup.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('flights:home')
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('flights:home'))
        else:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # Автоматически авторизуем пользователя после регистрации
        if form.is_valid():
            user = form
            user.save()
            login(self.request, user)
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class SignInView(FormView):
    template_name = 'user_management/auth.html'
    form_class = EmailAuthenticationForm
    success_url = reverse_lazy('flights:home')
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Вы уже вошли в систему.')
            return redirect('flights:home')
        else:
            return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        #form = EmailAuthenticationForm(self.request, data=self.request.POST)
        print(User.objects.all())
        if form.is_valid():
            user = form.get_user()
            print(user.mfa_enabled)
            if user.mfa_enabled:
                return redirect('user_management:verify_mfa', user_id=user.id)
            login(self.request, user)
            messages.success(self.request, f'Добро пожаловать!')
            return super().form_valid(form)
        return self.form_invalid(form)
        username = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        print(form.cleaned_data)
        user = authenticate(self.request, username=username, password=password)
        print(user)
        if user is not None:
            if user.mfa_enabled:
                return redirect('user_management:verify_mfa', user_id=user.id)
            login(self.request, user)
            messages.success(self.request, f'Добро пожаловать!')
            return super().form_valid(form)
        else:
            #messages.error(self.request, 'Неверное имя пользователя или пароль.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        print(User.objects.all())
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
        issuer_name='Bilety.ru'
    )
    print(user.mfa_secret)
    qr = qrcode.QRCode(version=1, box_size=10, border=5, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(otp_uri)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    qr_img.save('user_management/static/user_management/qr_code.png')
    qr_img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()
    

    qr_code_data_uri = f"data:image/png;base64,{qr_code}"

    return render(request, 'user_management/qrCodePage.html', {'qr_code': qr_code})


def verify_mfa(request, user_id):
    if request.method == 'POST':
        otp = request.POST.get('otp_code')
        if not user_id:
            messages.error(request, 'Неверный id пользователя')
            return render(request, 'user_management/otp_verify.html', {'user_id': user_id})
        user = User.objects.get(id=user_id)
        if verify_2fa_otp(user, otp):
            if request.user.is_authenticated:
                messages.success(request, '2-х факторная аутентификация включена!')
                return redirect('flights:home')
            login(request, user)
            messages.success(request, 'Вы вошли!')
            return redirect('flights:home')
        else:
            messages.error(request, 'Неверный код')
            if request.user.is_authenticated:
                return redirect('flights:home')
            return render(request, 'user_management/otp_verify.html', {'user_id': user_id})
            
    return render(request, 'user_management/otp_verify.html', {'user_id': user_id})
