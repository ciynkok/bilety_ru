from django.urls import path, include
from .views import index, SignUpView, SignInView, LogOutView, profile

app_name = 'user_management'

urlpatterns = [
    path('', index, name='index'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('logout/', LogOutView.as_view(), name='logout'),
    path('profile/', profile, name='profile'),
]
