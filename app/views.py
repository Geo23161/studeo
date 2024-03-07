from django.shortcuts import render
import json
from .models import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .tests import *
from .core import Kkiapay
import io
import fitz
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message as FCMMess , Notification, AndroidNotification, WebpushConfig, WebpushFCMOptions, AndroidConfig, APNSConfig, APNSPayload, Aps


IS_DEV = False

def getKkiapay():
    return Kkiapay(g_v('kkiapay0'+ (":sand" if IS_DEV else "")), g_v('kkiapay1'+ (":sand" if IS_DEV else "")), g_v('kkiapay2'+ (":sand" if IS_DEV else "")), sandbox= IS_DEV)

def send_notif_to_staff() :
    staffs = User.objects.filter(is_staff = True)
    devices = FCMDevice.objects.filter(user__in = staffs)
    for device in devices :
        device.send_message(
                    message = FCMMess(notification=Notification(title= "Nouvelle question", body= "Un utilisateur vient de poser une nouvelle question."),
                    )
                    
                )
        
def send_ready(user) :
    device = FCMDevice.objects.get(user = user)
    device.send_message(
                    message = FCMMess(notification=Notification(title= "Réponse prête", body= "Nous vous avons déjà envoyé une réponse à votre question, ouvrez l'application et allez dans la partie Compte pour voir vos demandes."),
                    )
                    
                )

# Create your views here.

@api_view(['GET'])
def get_annees(request) :
    return Response({
        'done' : True,
        'result' : AnneeSerializer(Annee.objects.all().order_by('niv'), many = True).data
    })


@api_view(['POST'])
def register(request) :
    prenom = request.data.get('prenom')
    email = request.data.get('email')
    password = request.data.get('password')
    annee = request.data.get('annee')

    if User.objects.filter(email = email).exists() : 
        return Response({
            'done' : False,
            'result' : 0
        })

    user = User.objects.create(prenom = prenom, email = email, annee = annee)
    user.set_password(password)
    user.save()

    abon = Abon.objects.create(user = user, typ = json.dumps(ABON_TYP[0]), state = False)
    

    return Response({
        'done' : True
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_home(request) :
    annee = Annee.objects.get(slug = request.user.annee)
    aides = annee.aides.all().union(Aides.objects.exclude(annee__slug = request.user.annee)).order_by('-created_at')[:15]
    conseils = annee.conseils.all().union(Conseils.objects.exclude(annee__slug = request.user.annee)).order_by('-created_at')[:15]
    fichiers = annee.fics.all().union(Fichiers.objects.exclude(annee__slug = request.user.annee)).order_by('-created_at')[:15]

    return Response({
        'done' : True,
        'result' : {
            'aides' : AidesSerializer(aides, many = True).data,
            'conseils' : ConseilsSerializer(conseils, many = True).data,
            'fichiers' : FichiersSerializer(fichiers, many = True).data
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_filters(request) :
    return Response({
        'done' : True,
        'result' : {
            'annees' : AnneeSerializer(Annee.objects.all().order_by('niv'), many = True).data,
            'matieres' : MatiereSerializer(Matiere.objects.all().order_by('niv'), many = True).data,
            'typefics' : TypeFicSerializer(TypeFic.objects.filter(format_of= request.GET.get('typ') ).order_by('niv'), many = True).data
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_aides(request) :
    filter_obj = json.loads(request.data.get('filt'))
    excep = json.loads(request.data.get('excep'))
    search_w = request.data.get('search_w', "")
    is_me = request.data.get('is_me')

    aides = Aides.objects.filter(pk= 0)
    
    if filter_obj['annee'] != '' :
        annee = Annee.objects.get(slug = filter_obj['annee'])
        aides_a = annee.aides.all()
    else :
        aides_a = Aides.objects.all()

    if filter_obj['matiere'] != '' :
        matiere = Matiere.objects.get(slug = filter_obj['matiere'])
        aides_m = matiere.aides.all()
    else :
        aides_m = Aides.objects.all()
    
    if filter_obj['typefic'] != '' :
        typefic = TypeFic.objects.get(slug = filter_obj['typefic'])
        aides_t = typefic.aides.all()
    else :
        aides_t = Aides.objects.all()
                                          
    aides = aides_a.intersection(aides_m).intersection(aides_t)
    aides = Aides.objects.filter(pk__in = [a.pk for a in aides ])
    if search_w != "" :
        aides = aides.filter(text__icontains = search_w)
    if is_me :
        aides = aides.filter(user__pk = request.user.pk)
        
    
    aides = aides.exclude(pk__in = excep)[:20]
    
    return Response({
        'done' : True,
        'result' : AidesSerializer(aides, many = True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_conseils(request) :
    filter_obj = json.loads(request.data.get('filt'))
    excep = json.loads(request.data.get('excep'))
    aides = Conseils.objects.filter(pk= 0)
    is_me = request.data.get('is_me')
    
    

    search_w = request.data.get('search_w', "")

    if filter_obj['annee'] != '' :
        annee = Annee.objects.get(slug = filter_obj['annee'])
        aides_a = annee.conseils.all()
    else :
        aides_a = Conseils.objects.all()

    if filter_obj['matiere'] != '' :
        matiere = Matiere.objects.get(slug = filter_obj['matiere'])
        aides_m = matiere.conseils.all()
    else :
        aides_m = Conseils.objects.all()
    
    if filter_obj['typefic'] != '' :
        typefic = TypeFic.objects.get(slug = filter_obj['typefic'])
        aides_t = typefic.conseils.all()
    else :
        aides_t = Conseils.objects.all()
                                          
    aides = aides_a.intersection(aides_m).intersection(aides_t)
    aides = Conseils.objects.filter(pk__in = [a.pk for a in aides ])
    if search_w != "" :
        aides = aides.filter(text__icontains = search_w)
    if is_me :
        aides = aides.filter(user__pk = request.user.pk)
    
    aides = aides.exclude(pk__in = excep)[:20]
    
    return Response({
        'done' : True,
        'result' : ConseilsSerializer(aides, many = True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_fichiers(request) :
    filter_obj = json.loads(request.data.get('filt'))
    excep = json.loads(request.data.get('excep'))
    aides = Fichiers.objects.filter(pk= 0)
    is_me = request.data.get('is_me')
    search_w = request.data.get('search_w', '')
    

    if filter_obj['annee'] != '' :
        annee = Annee.objects.get(slug = filter_obj['annee'])
        aides_a = annee.fics.all()
    else :
        aides_a = Fichiers.objects.all()

    if filter_obj['matiere'] != '' :
        matiere = Matiere.objects.get(slug = filter_obj['matiere'])
        aides_m = matiere.fics.all()
    else :
        aides_m = Fichiers.objects.all()
    
    if filter_obj['typefic'] != '' :
        typefic = TypeFic.objects.get(slug = filter_obj['typefic'])
        aides_t = typefic.fics.all()
    else :
        aides_t = Fichiers.objects.all()
        
    aides = aides_a.intersection(aides_m).intersection(aides_t)
    aides = Fichiers.objects.filter(pk__in = [a.pk for a in aides ])
    if search_w != "" :
        aides = aides.filter(text__icontains = search_w)
    if is_me :
        aides = aides.filter(user__pk = request.user.pk)
    
    aides = Fichiers.objects.filter(pk__in = [a.pk for a in aides ])
    aides = aides.exclude(pk__in = excep)[:20]
    
    return Response({
        'done' : True,
        'result' : FichiersSerializer(aides , many = True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_aides_answers(request) :
    aides_pk = [ a.aide.pk for a in request.user.answers_aides.all()]
    excep = json.loads(request.data.get('excep'))

    aides = Aides.objects.filter(pk__in = aides_pk).order_by('-created_at')

    aides = aides.exclude(pk__in = excep)[:20]
    
    return Response({
        'done' : True,
        'result' : AidesSerializer(aides , many = True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_conseils_answers(request) :
    aides_pk = [ a.conseil.pk for a in request.user.answers_conseils.all()]
    excep = json.loads(request.data.get('excep'))

    aides = Conseils.objects.filter(pk__in = aides_pk).order_by('-created_at')

    aides = aides.exclude(pk__in = excep)[:20]
    
    return Response({
        'done' : True,
        'result' : ConseilsSerializer(aides , many = True).data
    })
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_news(request) :
    excep = json.loads(request.data.get('excep'))
    news = News.objects.all().order_by('-created_at').exclude(pk__in = excep)[:10]


    return Response({
        'done' : True,
        'result' : NewsSerializer(news, many = True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_new(request) :
    id = request.data.get('id')
    return Response({
        'done' : True,
        'result' : NewsSerializer(News.objects.get(pk = int(id))).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_abons(self) :
    return Response({
        'done'  :True,
        'result': [ a for a in ABON_TYP if not 'Gratuit' in a['name']],
        'other' : [g_v('kkiapay0'), IS_DEV]
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activ_abon(request) :
    transactionId = request.data.get('transactionId')
    amount = request.data.get('amount')
    typ = json.loads(request.data.get('typ'))
    kkia = getKkiapay()
    if kkia.verify_transaction(transaction_id=transactionId).status == "SUCCESS" :
        pay = Payment.objects.create( transactionId = transactionId, amount = amount, user = request.user )
        abon = Abon.objects.create( user = request.user, pay = pay, typ = json.dumps(typ) )

        return Response({
            'done' : True,
            'result' : AbonSerializer(abon).data
        }) 
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pays(request) :
    return Response({
        'done' : True,
        'result' : PaymentSerializer(request.user.pays.all().order_by('-created_at'), many = True).data
    })

def file_model(typ) :
    return Image if typ == 'img' else (Audio if typ == 'aud' else Video)

def file_serializer(typ) :
    return ImageSerializer if typ == 'img' else (AudioSerializer if typ == 'aud' else VideoSerializer)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def charg_file(request) :
    typ = request.POST.get('typ')
    total = int(request.POST.get('total'))
    files = []
    previews = []
    finals = []
    for i in range(total) :
        files.append(request.FILES.get('file' + str(i)))
        if typ == 'vid' : previews.append(request.FILES.get('preview' + str(i)))
    cpt = 0
    for file in files :
        fil = file_model(typ).objects.create(file = file)
        if typ == 'vid' :
            fil.preview = previews[cpt]
            fil.save()
        if typ == 'aud' :
        
            fil.size = int(request.POST.get('size'))
            fil.save()
        cpt += 1
        finals.append(fil)
    
    return Response({
        'done' : True,
        'result' : file_serializer(typ)(finals, many = True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_aides(request) :
    filt = json.loads(request.data.get('filt'))
    text = request.data.get('text')
    audio = int(request.data.get('audio'))
    images = json.loads(request.data.get('images'))
    videos = json.loads(request.data.get('videos'))
    

    epr = request.GET.get('epr')
    if epr :
        epr = int(epr)
        images = [img.pk for img in Fichiers.objects.get(pk = epr).image.all()]

    aide = Aides.objects.create(text = text, user = request.user)
    
    annees = Annee.objects.filter(slug = filt['annee']) if filt['annee'] != '' else Annee.objects.all()
    for ann in annees :
        aide.annee.add(ann)
    
    annees = Matiere.objects.filter(slug = filt['matiere']) if filt['matiere'] != '' else Matiere.objects.all()
    for ann in annees :
        aide.matiere.add(ann)

    annees = TypeFic.objects.filter(slug = filt['typefic']) if filt['typefic'] != '' else TypeFic.objects.all()
    for ann in annees :
        aide.typefic.add(ann)

    if audio :
        aide.audio.add(Audio.objects.get(pk = audio))
    
    for img in images :
        aide.image.add(Image.objects.get(pk = img))

    for vid in videos :
        aide.video.add(Video.objects.get(pk = vid))

    send_notif_to_staff()

    return Response({
        'done' : True,
        'result' : aide.pk
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conseils(request) :
    filt = json.loads(request.data.get('filt'))
    text = request.data.get('text')
    audio = int(request.data.get('audio'))
    images = json.loads(request.data.get('images'))
    videos = json.loads(request.data.get('videos'))

    aide = Conseils.objects.create(text = text, user = request.user)
    
    annees = Annee.objects.filter(slug = filt['annee']) if filt['annee'] != '' else Annee.objects.all()
    for ann in annees :
        aide.annee.add(ann)
    
    annees = Matiere.objects.filter(slug = filt['matiere']) if filt['matiere'] != '' else Matiere.objects.all()
    for ann in annees :
        aide.matiere.add(ann)

    annees = TypeFic.objects.filter(slug = filt['typefic']) if filt['typefic'] != '' else TypeFic.objects.all()
    for ann in annees :
        aide.typefic.add(ann)

    if audio :
        aide.audio.add(Audio.objects.get(pk = audio))
    
    for img in images :
        aide.image.add(Image.objects.get(pk = img))

    for vid in videos :
        aide.video.add(Video.objects.get(pk = vid))

    send_notif_to_staff()

    return Response({
        'done' : True,
        'result' : aide.pk
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def charg_fiche(request) :
    
    files = []
    total = int(request.POST.get('total'))
    for i in range(total) :
        files.append(request.FILES.get('file' + str(i)))

    generateds = []

    
    for file in files :
        if 'pdf' in file.content_type :
            data = file.read()
            images = []
            doocument = fitz.open(stream = data, filetype="pdf")
            for page_num in range(len(doocument)) :
                page = doocument[page_num]
                image = page.get_pixmap().pil_tobytes(format="WEBP", optimize=True)
                uploaded_file = SimpleUploadedFile("filename.webp", image)
                img = Image.objects.create(name="pdf")
                img.file.save("filename.webp", uploaded_file)
                img.save()
                
                generateds.append(img)
        else :
            generateds.append(Image.objects.create(file = file))
    
    return Response({
        'done' : True,
        'result' : ImageSerializer(generateds, many = True).data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_fiches(request) :
    filt = json.loads(request.data.get('filt'))
    text = request.data.get('text')
    images = json.loads(request.data.get('images'))

    aide = Fichiers.objects.create(text = text, user = request.user)
    
    annees = Annee.objects.filter(slug = filt['annee']) if filt['annee'] != '' else Annee.objects.all()
    for ann in annees :
        aide.annee.add(ann)
    
    annees = Matiere.objects.filter(slug = filt['matiere']) if filt['matiere'] != '' else Matiere.objects.all()
    for ann in annees :
        aide.matiere.add(ann)

    annees = TypeFic.objects.filter(slug = filt['typefic']) if filt['typefic'] != '' else TypeFic.objects.all()
    for ann in annees :
        aide.typefic.add(ann)
    
    for img in images :
        aide.image.add(Image.objects.get(pk = img))

    return Response({
        'done' : True,
        'result' : aide.pk
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_aide(request, id) :
    return Response({
        'done' : True,
        'result' : AidesSerializer(Aides.objects.get(pk = id)).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conseil(request, id) :
    return Response({
        'done' : True,
        'result' : ConseilsSerializer(Conseils.objects.get(pk = id)).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fiche(request, id) :
    return Response({
        'done' : True,
        'result' : FichiersSerializer(Fichiers.objects.get(pk = id)).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_answer(request, id) :
    typ = request.GET.get('typ')
    aide = ( Aides if typ == 'aide' else Conseils).objects.get(pk= id).answers.all().order_by('-created_at')
    if not aide.count() :
        waiter = ( AnswerAides if typ == 'aide' else AnswerConseil).objects.create(text = "Un de nos expert est dessus! Donnez-nous un moment...")
        if typ == 'aide' :
            waiter.aide = ( Aides).objects.get(pk= id)
        else :
            waiter.conseil = (Conseils).objects.get(pk= id)
        waiter.save()

        aide.union( ( AnswerAides if typ == 'aide' else AnswerConseil).objects.filter(pk__in = [ waiter.pk]))
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)( f"{request.user.pk}m{request.user.pk}" , {
            'type' : 'register_room',
            'result' : typ + str(id),
        })
    return Response({
        'done' : True,
        'result' : (AnswerAidesSerializer if typ == 'aide' else AnswerConseilSerializer)(( Aides if typ == 'aide' else Conseils).objects.get(pk= id).answers.all().order_by('-created_at'), many = True).data,
        'is_prem' : request.user.is_staff
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aides_answers(request) :
    
    box = Aides.objects.get(pk = int(request.data.get('id')))
    text = request.data.get('text')
    audio = int(request.data.get('audio'))
    images = json.loads(request.data.get('images'))
    videos = json.loads(request.data.get('videos'))

    aide = AnswerAides.objects.create(text = text, user = request.user, aide = box)

    if audio :
        aide.audio.add(Audio.objects.get(pk = audio))
    
    for img in images :
        aide.image.add(Image.objects.get(pk = img))

    for vid in videos :
        aide.video.add(Video.objects.get(pk = vid))

    if request.user.is_staff :
        aide.type_of = 'solved'
    else :
        aide.type_of = 'question'
    aide.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)( 'aide' + str(box.pk) , {
            'type' : 'aide_answer',
            'result' : AnswerAidesSerializer(aide).data,
        })

    return Response({
        'done' : True,
        'result' : box.pk
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def conseils_answers(request) :
    
    box = Conseils.objects.get(pk = int(request.data.get('id')))
    text = request.data.get('text')
    audio = int(request.data.get('audio'))
    images = json.loads(request.data.get('images'))
    videos = json.loads(request.data.get('videos'))

    aide = AnswerConseil.objects.create(text = text, user = request.user, conseil = box)

    if audio :
        aide.audio.add(Audio.objects.get(pk = audio))
    
    for img in images :
        aide.image.add(Image.objects.get(pk = img))

    for vid in videos :
        aide.video.add(Video.objects.get(pk = vid))

    if request.user.is_staff :
        aide.type_of = 'solved'
        send_ready(aide.user)
    else :
        aide.type_of = 'question'
        send_notif_to_staff()
    aide.save()

    box.seen = False
    box.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)( 'conseil' + str(box.pk) , {
            'type' : 'conseil_answer',
            'result' : AnswerAidesSerializer(aide).data,
        })

    return Response({
        'done' : True,
        'result' : box.pk,

    })
    
    
@api_view(['GET', 'HEAD'])
@permission_classes([IsAuthenticated])
def ping(request):
    return Response({'done': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
def is_authorized(request) :
    typ = request.data.get('typ')
    id = int(request.data.get('id'))

    model = (Aides if typ == 'aide' else (Conseils if typ == 'conseil' else Fichiers)).objects.get(pk = id)
    
    is_me = model.user.pk == request.user.pk

    if not is_me : 
        global_can = request.user.cur_abn().state
    else :
        global_can = (Aides if typ == 'aide' else (Conseils if typ == 'conseil' else Fichiers)).objects.filter(user = request.user).filter(created_at__lt = timezone.now(), created_at__gt = (timezone.now() - timezone.timedelta(days=ABN_LIMIT[request.user.cur_abn().get_typ()['name']]['days']))).count() < ABN_LIMIT[request.user.cur_abn().get_typ()['name']]['limit']
    
    staff = 0

    if request.user.is_staff :
        if typ == 'aide' : 
            staff = StaffWork.objects.get_or_create(staff = request.user, aide = model)[0].pk

        elif typ == 'conseil' : 
            staff = StaffWork.objects.get_or_create(staff = request.user, conseil = model)[0].pk
    
    return Response({
        'done' : True,
        'result' : True if request.user.is_staff else global_can,
        'other' : {
            'staff' : staff,
            'working' : StaffWork.objects.filter(accepted = True, aide = model if typ == 'aide' else None, conseil = model if typ != 'aide' else None ).first().staff.pk if StaffWork.objects.filter(accepted = True).exists() else 0 
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
def set_working(request) :
    staff = StaffWork.objects.get(pk = int(request.data.get('id')))
    staff.accepted = not staff.accepted
    staff.save()

    return Response({
        'done' : True,
        'result' : {
            'staff' : staff.pk,
            'working' : StaffWork.objects.filter(accepted = True).first().staff.pk if StaffWork.objects.filter(accepted = True).exists() else 0 
        }
    })

