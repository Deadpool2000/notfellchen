import uuid

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import Group
from django.contrib.auth.models import AbstractUser

from fellchensammlung.tools import misc, geo
from notfellchen.settings import MEDIA_URL


class Language(models.Model):
    """Model representing a Language (e.g. English, French, Japanese, etc.)"""
    name = models.CharField(max_length=200,
                            help_text=_("Der Name einer natürliche Sprache wie Deutsch, Englisch oder Arabisch."),
                            unique=True)

    languagecode = models.CharField(max_length=10,
                                    # Translators: This helptext includes an URL
                                    help_text=_(
                                        "Der standartisierte Sprachcode. Mehr Informationen: http://www.i18nguy.com/unicode/language-identifiers.html"),
                                    verbose_name=_('Sprachcode'))

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

    class Meta:
        verbose_name = _('Sprache')
        verbose_name_plural = _('Sprachen')


class Image(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='images')
    alt_text = models.TextField(max_length=2000)

    def __str__(self):
        return self.title

    @property
    def as_html(self):
        return f'<img src="{MEDIA_URL}/{self.image}" alt="{self.alt_text}">'


class Species(models.Model):
    """Model representing a species of animal."""
    name = models.CharField(max_length=200, help_text=_('Name der Tierart'),
                            verbose_name=_('Name'))

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    class Meta:
        verbose_name = _('Tierart')
        verbose_name_plural = _('Tierarten')


class Location(models.Model):

    place_id = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    name = models.CharField(max_length=2000)

    def __str__(self):
        return f"{self.name} ({self.latitude:.5}, {self.longitude:.5})"

    @staticmethod
    def get_location_from_string(location_string):
        geo_api = geo.GeoAPI()
        get_geojson = geo_api.get_geojson_for_query(location_string)
        result = get_geojson[0]
        if "name" in result:
            name = result["name"]
        else:
            name = result["display_name"]
        location = Location.objects.create(
            place_id=result["place_id"],
            latitude=result["lat"],
            longitude=result["lon"],
            name=name,
        )
        return location


class RescueOrganization(models.Model):
    def __str__(self):
        return f"{self.name}"

    name = models.CharField(max_length=200)
    trusted = models.BooleanField(default=False, verbose_name=_('Vertrauenswürdig'))
    location_string = models.CharField(max_length=200, verbose_name=_("Ort der Organisation"))
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    instagram = models.URLField(null=True, blank=True, verbose_name=_('Instagram Profil'))
    facebook = models.URLField(null=True, blank=True, verbose_name=_('Facebook Profil'))
    fediverse_profile = models.URLField(null=True, blank=True, verbose_name=_('Fediverse Profil'))
    website = models.URLField(null=True, blank=True, verbose_name=_('Website'))


class AdoptionNotice(models.Model):
    class Meta:
        permissions = [
            ("create_active_adoption_notice", "Can create an active adoption notice"),
        ]

    def __str__(self):
        return f"{self.name}"

    created_at = models.DateField(verbose_name=_('Erstellt am'), default=datetime.now)
    searching_since = models.DateField(verbose_name=_('Sucht nach einem Zuhause seit'))
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, verbose_name=_('Beschreibung'))
    organization = models.ForeignKey(RescueOrganization, blank=True, null=True, on_delete=models.SET_NULL,
                                     verbose_name=_('Organisation'))
    further_information = models.URLField(null=True, blank=True, verbose_name=_('Link zu mehr Informationen'))
    group_only = models.BooleanField(default=False, verbose_name=_('Ausschließlich Gruppenadoption'))
    photos = models.ManyToManyField(Image, blank=True)
    location_string = models.CharField(max_length=200, verbose_name=_("Ortsangabe"))
    location = models.ForeignKey(Location, blank=True, null=True, on_delete=models.SET_NULL,)

    @property
    def animals(self):
        return Animal.objects.filter(adoption_notice=self)

    @property
    def comments(self):
        return Comment.objects.filter(adoption_notice=self)

    def get_absolute_url(self):
        """Returns the url to access a detailed page for the animal."""
        return reverse('adoption-notice-detail', args=[str(self.id)])

    def get_report_url(self):
        return reverse('report-adoption-notice', args=[str(self.id)])

    def get_photos(self):
        """
        First trys to get group photos that are attached to the adoption notice if there is none it trys to fetch
        them from the animals
        """
        group_photos = self.photos.all()
        if len(group_photos) > 0:
            return group_photos
        else:
            photos = []
            for animal in self.animals:
                photos.extend(animal.photos.all())
            if len(photos) > 0:
                return photos

    def get_photo(self):
        """
        Returns the first photo it finds.
        First trys to get group photos that are attached to the adoption notice if there is none it trys to fetch
        them from the animals
        """
        group_photos = self.photos.all()
        if len(group_photos) > 0:
            return group_photos[0]
        else:
            photos = []
            for animal in self.animals:
                photos.extend(animal.photos.all())
            if len(photos) > 0:
                return photos[0]


class Animal(models.Model):
    MALE_NEUTERED = "M_N"
    MALE = "M"
    FEMALE_NEUTERED = "F_N"
    FEMALE = "F"
    SEX_CHOICES = {
        MALE_NEUTERED: "neutered male",
        MALE: "male",
        FEMALE_NEUTERED: "neutered female",
        FEMALE: "female",
    }

    date_of_birth = models.DateField(verbose_name=_('Geburtsdatum'))
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, verbose_name=_('Beschreibung'))
    species = models.ForeignKey(Species, on_delete=models.PROTECT)
    photos = models.ManyToManyField(Image, blank=True)
    sex = models.CharField(max_length=20, choices=SEX_CHOICES, )
    adoption_notice = models.ForeignKey(AdoptionNotice, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"

    @property
    def age(self):
        return datetime.today().date() - self.date_of_birth

    @property
    def hr_age(self):
        """Returns a human-readable age based on the date of birth."""
        return misc.age_as_hr_string(self.age)

    def get_photo(self):
        """
        Selects a random photo from the animal
        """
        photos = self.photos.all()
        if len(photos) > 0:
            return photos[0]

    def get_photos(self):
        """
        Selects all photos from the animal
        """
        return self.photos.all()

    def get_absolute_url(self):
        """Returns the url to access a detailed page for the animal."""
        return reverse('animal-detail', args=[str(self.id)])


class Rule(models.Model):
    """
    Class to store rules
    """
    title = models.CharField(max_length=200)

    # Markdown is allowed in rule text
    rule_text = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    # Rule identifier allows to translate rules with the same identifier
    rule_identifier = models.CharField(max_length=24)

    def __str__(self):
        return self.title


class Report(models.Model):
    class Meta:
        permissions = []

    ACTION_TAKEN = "action taken"
    NO_ACTION_TAKEN = "no action taken"
    WAITING = "waiting"
    STATES = {
        ACTION_TAKEN: "Action was taken",
        NO_ACTION_TAKEN: "No action was taken",
        WAITING: "Waiting for moderator action",
    }
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text=_('ID dieses reports'),
                          verbose_name=_('ID'))
    status = models.CharField(max_length=30, choices=STATES)
    reported_broken_rules = models.ManyToManyField(Rule)
    user_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.status}]: {self.user_comment:.20}"

    def get_absolute_url(self):
        """Returns the url to access a detailed page for the report."""
        return reverse('report-detail', args=[str(self.id)])

    def get_reported_rules(self):
        return self.reported_broken_rules.all()

    def get_moderation_actions(self):
        return ModerationAction.objects.filter(report=self)


class ReportAdoptionNotice(Report):
    adoption_notice = models.ForeignKey("AdoptionNotice", on_delete=models.CASCADE)

    @property
    def reported_content(self):
        return self.adoption_notice


class ReportComment(Report):
    reported_comment = models.ForeignKey("Comment", on_delete=models.CASCADE)

    @property
    def reported_content(self):
        return self.reported_comment


class ModerationAction(models.Model):
    BAN = "user_banned"
    DELETE = "content_deleted"
    COMMENT = "comment"
    OTHER = "other_action_taken"
    NONE = "no_action_taken"
    ACTIONS = {
        BAN: "User was banned",
        DELETE: "Content was deleted",
        COMMENT: "Comment was added",
        OTHER: "Other action was taken",
        NONE: "No action was taken"
    }
    action = models.CharField(max_length=30, choices=ACTIONS.items())
    created_at = models.DateTimeField(auto_now_add=True)
    public_comment = models.TextField(blank=True)
    # Only visible to moderator
    private_comment = models.TextField(blank=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)

    # TODO: Needs field for moderator that performed the action

    def __str__(self):
        return f"[{self.action}]: {self.public_comment}"


"""
Membership
"""


class User(AbstractUser):
    pass


class Member(models.Model):
    """
    Model that holds a user's profile, including the django user model

    It is created upon creation of a new django user (see add_member)
    The trust levels act as permission system and can be displayed as a badge for the user
    """

    # Admins can perform all actions and have the highest trust associated with them
    # Moderators can make moderation decisions regarding the deletion of content
    # Coordinators can create adoption notices without them being checked
    # Members can create adoption notices that must be activated
    ADMIN = "admin"
    MODERATOR = "Moderator"
    COORDINATOR = "Koordinator*in"
    MEMBER = "Mitglied"
    TRUES_LEVEL = {
        ADMIN: "Administrator*in",
        MODERATOR: "Moderator*in",
        COORDINATOR: "Koordinator*in",
        MEMBER: "Mitglied",
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('Nutzer*in'))
    preferred_language = models.ForeignKey(Language, on_delete=models.PROTECT, null=True, blank=True,
                                           verbose_name=_('Bevorzugte Sprache'))
    trust_level = models.CharField(choices=TRUES_LEVEL, max_length=100, default=MEMBER)

    class Meta:
        verbose_name = _('Nutzer*in')
        verbose_name_plural = _('Nutzer*innen')

    @receiver(post_save, sender=User)
    def add_member(sender, instance, created, raw, using, **kwargs):
        if len(Member.objects.filter(user=instance)) != 1:
            Member.objects.create(user=instance)

    def __str__(self):
        return str(self.user)

    def get_absolute_url(self):
        return reverse("member-detail", args=[str(self.user.id)])


class Text(models.Model):
    """
    Base class to store markdown content
    """
    title = models.CharField(max_length=100)
    content = models.TextField(verbose_name="Inhalt")
    language = models.ForeignKey(Language, verbose_name="Sprache", on_delete=models.PROTECT)
    text_code = models.CharField(max_length=24, verbose_name="Text code", blank=True)

    class Meta:
        verbose_name = "Text"
        verbose_name_plural = "Texte"

    def __str__(self):
        return f"{self.title} ({self.language})"


class Announcement(Text):
    """
    Class to store announcements that should be displayed for all users
    """
    logged_in_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    publish_start_time = models.DateTimeField(verbose_name="Veröffentlichungszeitpunk")
    publish_end_time = models.DateTimeField(verbose_name="Veröffentlichungsende")
    IMPORTANT = "important"
    WARNING = "warning"
    INFO = "info"
    TYPES = {
        IMPORTANT: "important",
        WARNING: "warning",
        INFO: "info",
    }
    type = models.CharField(choices=TYPES, max_length=100, default=INFO)

    @property
    def is_active(self):
        return self.publish_start_time < timezone.now() < self.publish_end_time

    def __str__(self):
        return f"[{'🟢' if self.is_active else '🔴'}]{self.title} ({self.language})"

    @staticmethod
    def get_active_announcements(logged_in=False, language=None):
        if logged_in:
            all_active_announcements = [a for a in Announcement.objects.all() if a.is_active]
        else:
            all_active_announcements = [a for a in Announcement.objects.filter(logged_in_only=False) if a.is_active]
        if language is None:
            return all_active_announcements
        else:
            if logged_in:
                announcements_in_language = Announcement.objects.filter(language=language)
            else:
                announcements_in_language = Announcement.objects.filter(language=language, logged_in_only=False)
            active_announcements_in_language = [a for a in announcements_in_language if a.is_active]

            untranslated_announcements = []
            text_codes = [announcement.text_code for announcement in active_announcements_in_language]
            for announcement in all_active_announcements:
                if announcement.language != language and announcement.text_code not in text_codes:
                    untranslated_announcements.append(announcement)
            return active_announcements_in_language + untranslated_announcements



class Comment(models.Model):
    """
    Class to store comments in markdown content
    """
    user = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name=_('Nutzer*in'))
    created_at = models.DateTimeField(auto_now_add=True)
    adoption_notice = models.ForeignKey(AdoptionNotice, on_delete=models.CASCADE, verbose_name=_('AdoptionNotice'))
    text = models.TextField(verbose_name="Inhalt")
    reply_to = models.ForeignKey("self", verbose_name="Antwort auf", blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} at {self.created_at.strftime('%H:%M %d.%m.%y')}: {self.text:.10}"

    def get_report_url(self):
        return reverse('report-comment', args=[str(self.id)])

    @property
    def get_absolute_url(self):
        return self.adoption_notice.get_absolute_url()
