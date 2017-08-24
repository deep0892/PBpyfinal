from django.conf.urls import url
from TextToSpeech.views import pollyexotel,samedayexpiryIVR,getfinaldetails,hardcopyrecievalIVR

urlpatterns = [
    url(r'polly', pollyexotel),    
    url(r'samedayexpiryIVR', samedayexpiryIVR),
    url(r'finalcalldetails', getfinaldetails), 
    url(r'hardcopyrecievalIVR', hardcopyrecievalIVR), 
]
