from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Google login creates/updates client users by default."""

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return
        email = sociallogin.account.extra_data.get('email')
        if not email:
            return
        try:
            user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.role:
            user.role = User.Role.CLIENT
        user.first_name = data.get('first_name') or user.first_name
        user.last_name = data.get('last_name') or user.last_name
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        if not user.role:
            user.role = User.Role.CLIENT
            user.save(update_fields=['role'])
        return user
