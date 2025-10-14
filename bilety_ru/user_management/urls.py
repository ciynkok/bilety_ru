from django.urls import path, include
from .views import SignUpView, SignInView, LogOutView, profile, qrCodePage, verify_mfa

app_name = 'user_management'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('logout/', LogOutView.as_view(), name='logout'),
    path('profile/', profile, name='profile'),
    path('qrCodePage/', qrCodePage, name='qrCodePage'),
    path('verify_mfa/<int:user_id>', verify_mfa, name='verify_mfa')
]
