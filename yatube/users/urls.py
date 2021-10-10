from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.urls import path

from users.views import SignUp

app_name = 'users'

PASS_CHANGE_URL = 'password_change/'
PASS_RESET_URL = 'password_reset/'
PASS_RESET_BY_EMAIL_URL = 'reset/'

urlpatterns = [
    path('logout/',
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'),
    path('login/',
         LoginView.as_view(template_name='users/login.html'),
         name='login'),
    path('signup/', SignUp.as_view(), name='signup'),
    path(PASS_CHANGE_URL,
         PasswordChangeView.as_view(
             template_name='users/password_change_form.html'),
         name='password_change_form'),
    path("".join((PASS_CHANGE_URL, 'done/')),
         PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'),
         name='password_change_done'),
    path(PASS_RESET_URL,
         PasswordResetView.as_view(
             template_name='users/password_reset_form.html'),
         name='password_reset_form'),
    path("".join((PASS_RESET_URL, 'done/')),
         PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path("".join((PASS_RESET_BY_EMAIL_URL, 'done/')),
         PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'),
         name='password_reset_complete')
]
