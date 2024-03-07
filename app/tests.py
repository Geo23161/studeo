from django.test import TestCase

# Create your tests here.

ABON_TYP = [
    {
        'name' : 'Gratuit',
        "amount" : 0,
        "features" : []
    },
    {
        'name' : "Régulier",
        'amount' : 2500,
        'features' : ["3 demandes par semaine"]
    },
    {
        'name' : "Actif",
        'amount' : 5000,
        'features' : ["1 demande par jour"]
    },
    {
        'name' : "Intensif",
        'amount' : 10000,
        "features" : ['Nombre de demandes illimitées']
    }
]

ABN_LIMIT = {
    'Gratuit' : {
        'days' : 30,
        'limit' : 0
    },
    "Régulier" : {
        'days' : 7,
        'limit' : 3
    },
    "Actif" : {
        'days' : 1,
        'limit' : 1
    },
    "Intensif" : {
        'days' : 7,
        'limit' : 3
    }
}