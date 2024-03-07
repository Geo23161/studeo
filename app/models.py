from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from rest_framework import serializers
from .tests import *
import json
from cloudinary.models import CloudinaryField

# Create your models here.

def g_v(key : str) :
    return StudeDetails.objects.get(key = key).value

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(('superuser must have is_superuser set to True'))
        return self.create_user(email, password, **extra_fields)
    
class Payment(models.Model) :
    transactionId = models.CharField(max_length = 150, null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add= True)
    amount = models.IntegerField(default = 2500)
    user = models.ForeignKey("User", related_name = "pays", null = True, blank = True, on_delete = models.CASCADE)


class Abon(models. Model) :
    user = models.ForeignKey("User", related_name = "abons", null = True, blank = True, on_delete = models.CASCADE)
    pay = models.OneToOneField(Payment, related_name="abn", on_delete = models.CASCADE, null = True, blank = True)
    typ = models.TextField(null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add= True)
    state = models.BooleanField(default = True)

    def get_typ(self) :
        return json.loads(self.typ)

class User(AbstractBaseUser, PermissionsMixin) :
    prenom = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True)
    sex = models.CharField(null=True, blank=True, max_length=10)
    quart = models.TextField(null=True, blank=True)
    annee = models.CharField(max_length= 150, null = True, blank = True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    objects = CustomUserManager()
    created_at = models.DateTimeField(auto_now_add=True)
    last = models.DateTimeField(null=True, blank=True, default=timezone.now())

    def not_seens(self) :
        return {
            'aides' : [a.pk for a in self.maides.all() if not a.seen],
            'conseils' : [c.pk for c in self.mconseils.all() if not c.seen]
        }
    
    def get_annee(self) :
        return AnneeSerializer(Annee.objects.get(slug = self.annee)).data
    
    def cur_abn(self) :
        return self.abons.all().order_by('-created_at')[0] 


class Annee(models.Model) :
    name = models.CharField(max_length = 150, null = True, blank = True)
    slug = models.CharField(max_length = 150, null = True, blank = True)
    niv = models.IntegerField(default = 0)

class Matiere(models.Model) :
    name = models.CharField(max_length = 150, null = True, blank = True)
    slug = models.CharField(max_length = 150, null = True, blank = True)
    niv = models.IntegerField(default = 0)

class Etablissement(models.Model) :
    name = models.CharField(max_length = 150, null = True, blank = True)
    slug = models.CharField(max_length = 150, null = True, blank = True)
    niv = models.IntegerField(default = 0)

class TypeFic(models.Model) :
    name = models.CharField(max_length = 150, null = True, blank = True)
    slug = models.CharField(max_length = 150, null = True, blank = True)
    niv = models.IntegerField(default = 0)
    format_of = models.CharField(max_length = 150, default="fichiers")

class Image(models.Model) :
    file = models.ImageField(upload_to="images/")
    name = models.CharField(max_length = 50, null = True, blank = True)
    def get_file(self) :
        return self.file.url


class Video(models.Model) :
    file = CloudinaryField(resource_type='video', null=True, blank=True)
    preview = models.ImageField(upload_to="images/videos/")
    name = models.CharField(max_length = 50, null = True, blank = True)
    def get_file(self) :
        return self.file.url

    def get_preview(self) :
        return self.preview.url

class Audio(models.Model) :
    file = CloudinaryField(resource_type='', null=True, blank=True)
    name = models.CharField(max_length = 50, null = True, blank = True)
    size = models.IntegerField(default=60)
    def get_file(self) :
        return self.file.url
    


class QaN(models.Model) :
    
    price = models.IntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add= True)

class Aides(QaN) :
    annee = models.ManyToManyField(Annee, related_name= "aides",  null = True, blank = True)
    matiere = models.ManyToManyField(Matiere, related_name= "aides",  null = True, blank = True)
    typefic = models.ManyToManyField(TypeFic, related_name= "aides",  null = True, blank = True)
    image = models.ManyToManyField(Image, null = True, related_name= "aides",  blank = True)
    audio = models.ManyToManyField(Audio, related_name= "aides",  null = True, blank = True)
    video = models.ManyToManyField(Video, related_name= "aides",  null = True, blank = True)
    text = models.TextField(null = True, blank = True)
    solved = models.BooleanField(default = False)
    views = models.ManyToManyField(User, related_name="aides")
    seen = models.BooleanField(default = False)
    user = models.ForeignKey(User, related_name="maides", on_delete = models.CASCADE, null = True, blank= True)
    def get_views(self) :
        return self.views.count()
    
class Conseils(QaN) :
    annee = models.ManyToManyField(Annee, related_name= "conseils",  null = True, blank = True)
    matiere = models.ManyToManyField(Matiere, related_name= "conseils",  null = True, blank = True)
    typefic = models.ManyToManyField(TypeFic, related_name= "conseils",  null = True, blank = True)
    image = models.ManyToManyField(Image, null = True, related_name= "conseils",  blank = True)
    audio = models.ManyToManyField(Audio, related_name= "conseils",  null = True, blank = True)
    video = models.ManyToManyField(Video, related_name= "conseils",  null = True, blank = True)
    text = models.TextField(null = True, blank = True)
    solved = models.BooleanField(default = False)
    user = models.ForeignKey(User, related_name="mconseils", on_delete = models.CASCADE, null = True, blank= True)
    views = models.ManyToManyField(User, related_name="conseils")
    seen = models.BooleanField(default = False)

    def get_views(self) :
        return self.views.count()
    
class Fichiers(QaN) :
    annee = models.ManyToManyField(Annee, related_name= "fics",  null = True, blank = True)
    matiere = models.ManyToManyField(Matiere, related_name= "fics",  null = True, blank = True)
    typefic = models.ManyToManyField(TypeFic, related_name= "fics",  null = True, blank = True)
    image = models.ManyToManyField(Image, null = True, related_name= "fics",  blank = True)
    audio = models.ManyToManyField(Audio, related_name= "fics",  null = True, blank = True)
    video = models.ManyToManyField(Video, related_name= "fics",  null = True, blank = True)
    text = models.TextField(null = True, blank = True)
    views = models.ManyToManyField(User, related_name="fichiers")
    seen = models.BooleanField(default = False)
    user = models.ForeignKey(User, related_name="mfics", on_delete = models.CASCADE, null = True, blank= True)
    
    def get_views(self) :
        return self.views.count()
    


class AnswerAides(models.Model) :
    user = models.ForeignKey(User, related_name="answers_aides", on_delete = models.CASCADE, null = True, blank= True)
    aide = models.ForeignKey(Aides, related_name="answers", on_delete = models.CASCADE, null = True, blank = True)
    image = models.ManyToManyField(Image, null = True,  blank = True)
    audio = models.ManyToManyField(Audio,   null = True, blank = True)
    video = models.ManyToManyField(Video,  null = True, blank = True)
    text = models.TextField(null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add= True)
    type_of = models.CharField(max_length=150, default = "waiter")
    views = models.ManyToManyField(User, related_name="answers_a")

class AnswerConseil(models.Model) :
    image = models.ManyToManyField(Image, null = True,  blank = True)
    audio = models.ManyToManyField(Audio,   null = True, blank = True)
    video = models.ManyToManyField(Video,  null = True, blank = True)
    text = models.TextField(null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add= True)
    type_of = models.CharField(max_length=150, default = "waiter")
    user = models.ForeignKey(User, related_name="answers_conseils", on_delete = models.CASCADE, null = True, blank= True)
    conseil = models.ForeignKey(Conseils, related_name="answers", on_delete = models.CASCADE, null = True, blank = True)
    views = models.ManyToManyField(User, related_name="answers_c")

class News(models.Model) :
    title = models.TextField(null = True, blank= True)
    image = models.ForeignKey(Image, related_name="for_news", on_delete = models.CASCADE, null = True, blank = True)
    text = models.TextField(null = True, blank = True)
    seen = models.ManyToManyField(User, related_name="has_seens")
    created_at = models.DateTimeField(auto_now_add= True)

    def get_image(self) :
        return self.image.url

    def get_seens(self) :
        return self.seen.count()
    
class StudeDetails(models.Model) :
    key = models.CharField(max_length = 150, null = True, blank = True)
    value = models.TextField(null = True, blank = True)


class StaffWork(models.Model) :
    staff = models.ForeignKey(User, related_name="works", on_delete = models.CASCADE, null = True, blank = True)
    aide = models.OneToOneField(Aides, related_name = "staffs", on_delete = models.CASCADE, null = True, blank = True )
    conseil = models.OneToOneField(Conseils, related_name = "staffs", on_delete = models.CASCADE, null = True, blank = True )
    created_at = models.DateTimeField(auto_now_add = True)
    accepted = models.BooleanField(default = False)


#Serializers
class NewsSerializer(serializers.ModelSerializer) :

    class Meta :
        model = News
        fields = ('id', 'title', 'get_image', 'text', 'get_seens')

class AudioSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Audio
        fields = ('id', 'get_file', 'size')

class ImageSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Image
        fields = ('id', 'get_file')

class VideoSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Video
        fields = ('id', 'get_file', 'get_preview')
    
class AnneeSerializer(serializers.ModelSerializer) :
    
    class Meta :
        model = Annee
        fields = ('id', 'name', 'slug')

class MatiereSerializer(serializers.ModelSerializer) :
    
    class Meta :
        model = Matiere
        fields = ('id', 'name', 'slug')

class EtablissementSerializer(serializers.ModelSerializer) :
    
    class Meta :
        model = Etablissement
        fields = ('id', 'name', 'slug')

class TypeFicSerializer(serializers.ModelSerializer) :
    
    class Meta :
        model = TypeFic
        fields = ('id', 'name', 'slug')

class AidesSerializer(serializers.ModelSerializer) :
    annee = AnneeSerializer(many = True)
    matiere = MatiereSerializer(many  =True)
    typefic = TypeFicSerializer(many = True)
    audio = AudioSerializer(many = True)
    image = ImageSerializer(many = True)
    video = VideoSerializer(many = True)
    class Meta :
        model = Aides
        fields = ('id', 'annee', 'matiere', 'typefic', 'image', 'audio', 'video', 'get_views', 'text', 'price', 'solved')


class ConseilsSerializer(serializers.ModelSerializer) :
    annee = AnneeSerializer(many = True)
    matiere = MatiereSerializer(many  =True)
    typefic = TypeFicSerializer(many = True)
    audio = AudioSerializer(many = True)
    image = ImageSerializer(many = True)
    video = VideoSerializer(many = True)
    class Meta :
        model = Conseils
        fields = ('id', 'annee', 'matiere', 'typefic', 'image', 'audio', 'video', 'get_views', 'text', 'price', 'solved')

class FichiersSerializer(serializers.ModelSerializer) :
    annee = AnneeSerializer(many = True)
    matiere = MatiereSerializer(many = True)
    typefic = TypeFicSerializer(many = True)
    audio = AudioSerializer(many = True)
    image = ImageSerializer(many = True)
    video = VideoSerializer(many = True)
    class Meta :
        model = Fichiers
        fields = ('id', 'annee', 'matiere', 'typefic', 'image', 'audio', 'video', 'get_views', 'text', 'price')

class PaymentSerializer(serializers.ModelSerializer) :

    class Meta :
        model = Payment
        fields = ('id', 'transactionId', 'created_at', 'amount')

class AbonSerializer(serializers.ModelSerializer) :
    pay = PaymentSerializer()
    class Meta :
        model = Abon
        fields = ('id', 'pay', 'get_typ', 'created_at', 'state')

class UserSerializer(serializers.ModelSerializer) :
    cur_abn = AbonSerializer()
    class Meta :
        model = User
        fields = ('id', 'prenom', 'email', 'get_annee', 'cur_abn')

class AnswerAidesSerializer(serializers.ModelSerializer) :
    audio = AudioSerializer(many = True)
    image = ImageSerializer(many = True)
    video = VideoSerializer(many = True)
    user = UserSerializer()
    class Meta :
        model = AnswerAides
        fields = ('id', 'audio', 'image', 'video', 'text', 'type_of', 'user' )

class AnswerConseilSerializer(serializers.ModelSerializer) :
    audio = AudioSerializer(many = True)
    image = ImageSerializer(many = True)
    video = VideoSerializer(many = True)
    user = UserSerializer()
    class Meta :
        model = AnswerConseil
        fields = ('id', 'audio', 'image', 'video', 'text', 'type_of', 'user' )
