import requests,os,json,time
from django.shortcuts import render
from django.http import HttpResponse


config  = open('config.txt', 'r')
data= config.read().split('\n')
appid=data[0]
userid=data[1]

def index(request):
     return render(request,"index.html")

def sessionstatus(sessionid):
    headers = {'Authorization' : appid }
    params = {'app_session_id' : sessionid}
    url = 'https://dev.liv.ai/liv_speech_api/session/status/'
    res = requests.get(url, headers = headers, params = params)
    print(res.content)
    docstatus=json.loads(res.content)
    transcribe=docstatus['transcribed_status']
    print(transcribe)
    return transcribe
    


def transcription(request):
    if request.method=="POST" and request.FILES['audio']:
        files = request.FILES.getlist('audio')

        transcript=[]

        for audio in files:
            filedata=audio.read()
            destination = open('test.mp3', 'wb')
            
            for chunk in audio.chunks():
                destination.write(chunk)
            destination.close()
            
            files = {'audio_file' : open('test.mp3','rb')}
            
            headers = {'Authorization' : appid}
            data = {'user' : userid ,'language' : 'EN','transcribe' : 1} #Change EN to HI if you want transcript in hindi
            
            url = 'https://dev.liv.ai/liv_speech_api/recordings/'
            res = requests.post(url, headers = headers, data = data, files = files)
            print(res.content)
            
            upload_result=json.loads(res.content)
            
            sessionid=upload_result['app_session_id']
            transcribe=False
            
            while transcribe==False:
                time.sleep(3)
                transcribe=sessionstatus(sessionid)
                
            headers = {'Authorization' : appid }
            params = {'app_session_id' : sessionid  }
            url = 'https://dev.liv.ai/liv_speech_api/session/transcriptions/'
            res = requests.get(url, headers = headers, params = params)
            t=json.loads(res.content)
            print(t)
            transcript.append(t['transcriptions'][0]['utf_text'])

        print(transcript)    
        return render(request,"long_audio.html",{'results':transcript})

    return render(request,"long_audio.html")


def tagssessionstatus(sessionid):
    headers = {'Authorization' : appid}
    params = {'app_session_id' : sessionid}
    url = 'https://dev.liv.ai/liv_speech_api/session/status/'
    res = requests.get(url, headers = headers, params = params)
    print(res.content)
    upload_result = json.loads(res.content)
    upload_status = upload_result['upload_status']
    tags_status = upload_result['tags_status']
    return tags_status 

def registertag():
    headers = {'Authorization' : appid}
    data = {'user' : '13170', 'language' : 'EN'}
    files = {'tag_file' : open('tags.txt','rb')}
    url = 'https://dev.liv.ai/liv_speech_api/tags/'
    res = requests.post(url, headers = headers, data = data, files = files)
    print(res.content)
    upload_result = json.loads(res.content)
    status =  upload_result["status"]
    print(status)
    
    if status == "success":
        return True 
    



def tags(request):
    if request.method=="POST" and request.FILES['audio']:
        
        audio = request.FILES['audio']
        tagnames = request.POST.get("tagnames")
        tagnames =tagnames.split()

        f = open('tags.txt','w')
        f.write("add\n")
        with open("tags.txt", "w") as text_file:
            for tagname in tagnames:
                text_file.write(tagname + "\n")
            print("done")

        f.close()


        registertag()

        filedata = audio.read()
        destination = open('test.mp3', 'wb')
        
        for chunk in audio.chunks():
            destination.write(chunk)
        destination.close()

        
        headers = {'Authorization' : appid}
        data = {'user' : '13170' ,'language' : 'EN'}
        files = {'audio_file' : open('test.mp3','rb')}
        url = 'https://dev.liv.ai/liv_speech_api/recordings/'
        res = requests.post(url, headers = headers, data = data, files = files)
        print(res.content)
        
        upload_result = json.loads(res.content)
        session_id = upload_result['app_session_id']
        print(session_id)
        time.sleep(3)
        upload_status = tagssessionstatus(session_id)
        
        while upload_status==False:
            time.sleep(3)
            upload_status = tagssessionstatus(session_id)
            
        headers = {'Authorization' : appid}
        params = {'app_session_id' : session_id }
        url = 'https://dev.liv.ai/liv_speech_api/session/tags/'
        res = requests.get(url, headers = headers, params = params)
        print(res.content)

        upload_result = json.loads(res.content)
        tags = upload_result['tags']
        print(tags)
        return render(request,"tags.html",{'results':tags})

    return render(request,"tags.html")


def transcriptionchat(request):
    if request.method=="POST" and request.FILES['agentaudio'] and request.FILES['customeraudio']:
         audio=request.FILES['agentaudio']
         splittime = request.POST.get("splittime")

         splittime = int(splittime)

         filedata=audio.read()
         
         destination = open('test.mp3', 'wb')
         
         for chunk in audio.chunks():
             destination.write(chunk)
         destination.close()
 
         files = {'audio_file' : open('test.mp3','rb')}
 
         headers = {'Authorization' : appid}
         data = {'user' : userid ,'language' : 'EN','transcribe' : 1} #Change EN to HI if you want transcript in hindi
 
         url = 'https://dev.liv.ai/liv_speech_api/recordings/'
         res = requests.post(url, headers = headers, data = data, files = files)
         print(res.content)
 
         upload_result=json.loads(res.content)
 
         sessionid=upload_result['app_session_id']
 
         transcribe=False
 
         while transcribe==False:
             time.sleep(3)
             transcribe=sessionstatus(sessionid)
 
 
 
         headers = {'Authorization' : appid }
         params = {'app_session_id' : sessionid  }
         url = 'https://dev.liv.ai/liv_speech_api/session/transcriptions/'
         res = requests.get(url, headers = headers, params = params)
         transcript=json.loads(res.content)
         #print(transcript)
         
         agentaudio = transcript['transcriptions'][0]['utf_text']
         agentwordinfo = transcript['transcriptions'][0]['per_word_info']
         #print(agentwordinfo)

         lineindex=[]
         start=agentwordinfo[0][1]
         #print(start)
         for info in agentwordinfo:
            if (info[1] - start >= splittime):
                 start = info[1]
                 lineindex.append(info[0]-1)
        
         #print(lineindex)

         temp = agentaudio.split()

         #print(temp)

         agentspeech = []
         agentspeech.append('')

         line = 0
         
         for i in range(len(temp)):
             agentspeech[line] = agentspeech[line]+ " " + temp[i]
             if line < len(lineindex) and i == lineindex[line]:
                 line = line+1
                 agentspeech.append('')
        
         #print(agentaudio)
         #print(agentspeech)





         





         audio=request.FILES['customeraudio']
         filedata=audio.read()
         
         destination = open('test.mp3', 'wb')
         
         for chunk in audio.chunks():
             destination.write(chunk)
         destination.close()
 
         files = {'audio_file' : open('test.mp3','rb')}
 
         headers = {'Authorization' : appid}
         data = {'user' : userid ,'language' : 'EN','transcribe' : 1} #Change EN to HI if you want transcript in hindi
 
         url = 'https://dev.liv.ai/liv_speech_api/recordings/'
         res = requests.post(url, headers = headers, data = data, files = files)
         print(res.content)
 
         upload_result=json.loads(res.content)
 
         sessionid=upload_result['app_session_id']
 
         transcribe=False
 
         while transcribe==False:
             time.sleep(3)
             transcribe=sessionstatus(sessionid)
 
 
 
         headers = {'Authorization' : appid }
         params = {'app_session_id' : sessionid  }
         url = 'https://dev.liv.ai/liv_speech_api/session/transcriptions/'
         res = requests.get(url, headers = headers, params = params)
         transcript=json.loads(res.content)
         #print(transcript)

         customeraudio=transcript['transcriptions'][0]['utf_text']
         customerwordinfo = transcript['transcriptions'][0]['per_word_info']
         print(customerwordinfo)

         lineindex = []
         start = customerwordinfo[0][1]
         #print(start)
         for info in customerwordinfo:
            if (info[1] - start >= splittime):
                 start = info[1]
                 lineindex.append(info[0]-1)
        
         #print(lineindex)

         temp = customeraudio.split()

         #print(temp)

         customerspeech = []
         customerspeech.append('')

         line = 0
         
         for i in range(len(temp)):
             customerspeech[line] = customerspeech[line]+ " " + temp[i]
             if line < len(lineindex) and i == lineindex[line]:
                 line = line+1
                 customerspeech.append('')
        
         #print(customeraudio)
         #print(customerspeech)

         chat = zip(agentspeech, customerspeech)

         print(chat)

 
 
         return render(request,"longaudiochat.html",{'chat' : chat})
 
    return render(request,"longaudiochat.html") 