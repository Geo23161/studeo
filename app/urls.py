from django.urls import path
from .views import *
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from rest_framework.routers import DefaultRouter
from django.urls.conf import include

router = DefaultRouter()
router.register('devices', FCMDeviceAuthorizedViewSet)

urlpatterns = [
    path('get_annees/', get_annees),
    path('register/', register),
    path('get_home/', get_home),
    path('get_filters/', get_filters),
    path('get_aides/', get_aides),
    path('get_conseils/', get_conseils),
    path('get_fichiers/', get_fichiers),
    path('get_aides_answers/', get_aides_answers),
    path('get_conseils_answers/' ,get_conseils_answers),
    path('get_news/', get_news),
    path('get_new/', get_new),
    path('get_abons/', get_abons),
    path('activ_abon/', activ_abon),
    path('get_pays/', get_pays),
    path('charg_file/', charg_file),
    path('create_aides/', create_aides),
    path('create_conseils/' ,create_conseils),
    path('charg_fiche/', charg_fiche),
    path('create_fiches/', create_fiches),
    path('get_aide/<int:id>/', get_aide),
    path('get_conseil/<int:id>/', get_conseil),
    path('get_fiche/<int:id>/', get_fiche),
    path('get_answer/<int:id>/', get_answer),
    path('conseils_answers/', conseils_answers),
    path('aides_answers/', aides_answers),
    path('ping/', ping, name="ping"),
    path('is_authorized/' ,is_authorized),
    path('set_working/', set_working)
]
