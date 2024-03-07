from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from .models import *
from django.utils import timezone

class UserConsumer(JsonWebsocketConsumer) :
    
    def connect(self) :
        if self.scope['user'].is_anonymous:
            return self.close()
        
        self.accept()
        async_to_sync(self.channel_layer.group_add)(f"{self.scope['user'].pk}m{self.scope['user'].pk}", self.channel_name)
        self.scope['user'].last = timezone.now()
        print(self.scope['user'].not_seens())
        done = {
            'notifs' : self.scope['user'].not_seens(),
            'user' : UserSerializer(self.scope['user']).data
        }

        async_to_sync(self.channel_layer.group_send)(f"{self.scope['user'].pk}m{self.scope['user'].pk}", {
            'type' : 'initialisation',
            'result' : done
        })

    def register_room(self, ev) :
        async_to_sync(self.channel_layer.group_add)(ev['result'], self.channel_name)
    
    def initialisation(self, ev) :
        return self.send_json(ev)

    def conseil_answer(self, ev) :
        return self.send_json(ev)
    
    def aide_answer(self, ev) :
        return self.send_json(ev)
    
    def aide_answer(self, ev) :
        print(ev)
        return self.send_json(ev)
        
    def receive_json(self, content, **kwargs):
        user = User.objects.get(pk = self.scope['user'].pk)
        if content['type'] == 'heartbeat' :
            user.last = timezone.now()
            user.save()
            
        elif content['type'] == 'o_aide' :
            aide = Aides.objects.get(pk = int(content['result']))
            if not user in aide.views.all() : aide.views.add(user)
            for ans in aide.answers.all() : ans.views.add(user)
        elif content['type'] == 'o_conseil' :
            aide = Conseils.objects.get(pk = int(content['result']))
            if not user in aide.views.all() : aide.views.add(user)
            for ans in aide.answers.all() : ans.views.add(user)
        elif content['type'] == 'o_fiche' :
            aide = Fichiers.objects.get(pk = int(content['result']))
            if not user in aide.views.all() : aide.views.add(user)
            for ans in aide.answers.all() : ans.views.add(user)

    def disconnect(self, code):
        if self.scope['user'].is_anonymous:
            return self.close()
