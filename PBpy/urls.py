"""PBpy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin
from NLU.views import result
#from TextToSpeech.views import get_url,saveExotelResponse
from TextToSpeech.views import pollyexotel,samedayexpiryIVR,getfinaldetails,hardcopyrecievalIVR,hardcopycallbackIVR,get_url,saveExotelResponse,maptoSP
from OCR.views import addDocument,query,get_doc_status,fileupload
from livai.views import transcription, tags,transcriptionchat, index,registertag


#from rest_framework import routers

#router = routers.DefaultRouter()
#router.register(r'users', UserViewSet)


urlpatterns = [
    #url(r'^', include(router.urls)),
    #url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^texttospeech/polly',pollyexotel ),
    url(r'^texttospeech/geturl',get_url ),
    url(r'^texttospeech/callresponse', saveExotelResponse),
    url(r'^texttospeech/samedayexpiryIVR',samedayexpiryIVR ),
    url(r'^texttospeech/finalcalldetails',getfinaldetails ),
    url(r'^texttospeech/hardcopyrecievalIVR',hardcopyrecievalIVR ),
    url(r'^texttospeech/hardcopycallbackIVR',hardcopycallbackIVR ),
    url(r'^texttospeech/spmap',maptoSP ),
    url(r'^ocr/adddoc', addDocument),
    url(r'^ocr/query', query),
    url(r'^ocr/docstatus',get_doc_status ),
    url(r'^ocr/upload',fileupload ),
    url(r'^nlu/querydocument',result ),
    
    url(r'^livai/transcription/', transcription),
    url(r'^livai/tags/', tags),
    url(r'^livai/chat/', transcriptionchat),
    url(r'^livai/registertag/', registertag),
    url(r'livai/^', index),

]
