from django.urls import path
from django.contrib.auth import views as auth_views #as auth_views to not mix them with other views
from . import views


app_name = "accounts"

urlpatterns = [
    path("reset_password/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("reset_password/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset_password/<uidb64>/<token>/", auth_views.PasswordResetView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("farmers/", views.FarmerList.as_view(), name="user_list"),
    path("user/<int:pk>/", views.UserDetail.as_view(), name="user_detail"),
    path("<int:pk>/update/", views.UpdateUser.as_view(), name="update_user"),
    path("<int:pk>/delete/", views.DeleteUser.as_view(), name="delete_user"),
    path("username_available/", views.CheckUsername.as_view(), name="check_username"),
]