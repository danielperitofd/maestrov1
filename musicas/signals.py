from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Profile
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount

@receiver(post_save, sender=User)
def create_profiles(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        Profile.objects.get_or_create(user=instance)

@receiver(user_signed_up)
def create_profile_on_google_signup(request, user, **kwargs):
    Profile.objects.get_or_create(user=user)

@receiver(user_signed_up)
def create_profile_on_google_signup(request, user, **kwargs):
    profile, created = Profile.objects.get_or_create(user=user)

    # Tenta puxar a foto do Google
    try:
        social_account = SocialAccount.objects.get(user=user, provider='google')
        photo_url = social_account.extra_data.get('picture')
        if photo_url:
            profile.photo_url = photo_url  # você pode criar esse campo como CharField no Profile
            profile.save()
    except SocialAccount.DoesNotExist:
        pass