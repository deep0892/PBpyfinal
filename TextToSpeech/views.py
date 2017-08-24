from __future__ import unicode_literals
import requests
from contextlib import closing
import datetime
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
import os.path
import json
import pyodbc
import xml.etree.ElementTree as ET
from django.http import HttpResponseRedirect
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
import base64
from django.contrib.auth import authenticate
import urllib
from pymongo import MongoClient

BASE = os.path.dirname(os.path.abspath(__file__))


url = 'mongodb://10.0.8.62:27017/'
client = MongoClient(url)


db = client.communicationDB

#connect to sql database

collection=db.PythonAPISettings
sqlconfig=collection.find_one({"type":"sqldatabaseconfig"})
print(sqlconfig)
sql_username=sqlconfig["username"]
sql_password=sqlconfig["password"]
sql_db=sqlconfig["db"]
sql_datasource=sqlconfig["datasource"]
sql_con_string ='DRIVER=FreeTDS;DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (sql_datasource, sql_username, sql_password ,sql_db)


def save_res(leadId,customerId,Policyno,Insurer,mobileno,url,sid):
    print("saving")
    conn = pyodbc.connect(sql_con_string)
    print(conn)
    cursor = conn.cursor()
    print(cursor)
    
    #url=url+"&filename=xyz.mp3"    
    query="INSERT INTO PBCROMA.MTX.VOICEURLDATA(callsid,leadid,customerid,policyno,insurer,mobileno,url) VALUES ('"+sid+"',"+leadId+","+customerId+",'"+Policyno+"','"+Insurer+"',"+mobileno+",'"+url+"');"
    print("below query")
    print(query)
    cursor.execute(query)
    conn.commit()
    print("saved to database")
    return


def geturl(filename,leadId,customerId):
    url = "https://api.policybazaar.com/cs/repo/uploadPolicyCopy?metaDataJson={leadId:"+leadId+",customerId:"+customerId+",productId:0,referenceNo:0}"
    files = {'file': (filename,open(filename, 'rb'),'audio/mp3')}
    r = requests.post(url,files=files)
    print(r)
    doc=json.loads(r.content)
    docurl=doc["policyCopyDetails"]["policyDocUrl"]
    return docurl


def save_polly(policyno, insurer,leadid,customerId):
    collection=db.PythonAPISettings
    polly_config=collection.find_one({"type":"pollyconfig"})
    print(polly_config)

    region=polly_config["region_name"]
    accesskey=polly_config["aws_access_key_id"]
    secretkey=polly_config["aws_secret_access_key"]

    session = Session(region_name=region,aws_access_key_id=accesskey,aws_secret_access_key=secretkey)
    polly = session.client("polly")
    policyno=str(policyno)
    insurer=str(insurer)

    collection=db.PythonAPISettings
    speech_config=collection.find_one({"type":"speechconfig"})
    speech=speech_config["speech"]
    print(speech)

    f=speech.split('$')


    text = f[0]+insurer+f[1]+policyno+f[2]
    print(text)
    response = polly.synthesize_speech(Text=text,VoiceId="Raveena",OutputFormat="mp3",TextType="ssml")
    print(response)
    stream=response.get("AudioStream")
    if stream:
        data=stream.read()
        filename=os.path.join(BASE, "voices/"+policyno+str(datetime.datetime.now())+".mp3")
        filename=filename.replace(" ", "")
        with open(filename, 'wb') as f:
            f.write(data)
            print("File Saved")
            f.close()
        docurl=geturl(filename,leadid,customerId)
        return docurl



def give_a_call(mobileno,appidsource=''):  

    collection=db.PythonAPISettings
    exotel_config=collection.find_one({"type":"exotelconfig"})
    print(exotel_config)
    
    url=exotel_config["url"]
    CallerId=exotel_config["callerid"]
    CallType=exotel_config["calltype"]
    auth=exotel_config["Authorization"]



    if appidsource=='':
        appid=exotel_config["appid"]
    elif appidsource=='SDE':
        appid=exotel_config["appid_SDE"]
    else:
        appid=exotel_config["appid_HCR"]
    
    print(appid)
 
    print("calling calling calling.....")
    
    headers = {
               "Authorization":auth,
               "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
               "From":mobileno,
               "CallerId":CallerId,
               "Url":"http://my.exotel.in/exoml/start/"+appid,
               "CallType": CallType
    }
    r=requests.post(url, headers=headers, data=payload)
    print(r)
    res=r.content
    root = ET.fromstring(res)
    sid=root[0][0].text
    print(sid)    
    return sid


@api_view(['POST'])
def pollyexotel(request):
    data=request.data
    try:
        leadId=data["leadId"]
        customerId=data["customerId"]
        policyno=data["policyno"]
        insurer=data["insurer"]
        mobileno=data["mobileno"]
    except:
        return HttpResponse(status=400)
    url=save_polly(policyno,insurer,leadId,customerId)
    sid=give_a_call(mobileno)
    save_res(leadId,customerId,policyno,insurer,mobileno,url,sid)   
    return Response(status=status.HTTP_200_OK)

@api_view(['POST'])
def samedayexpiryIVR(request):    
    data=request.data
    try:
        leadId=data["leadId"]
        customerId=data["customerId"]        
        mobileno=data["mobileno"]
    except:
        return HttpResponse(status=400)    
    sid=give_a_call(mobileno,"SDE")  
    save_res(leadId,customerId,'','',mobileno,'',sid)   
    return Response(status=status.HTTP_200_OK)    


@api_view(['GET'])
def get_url(request):
         try:
             auth_header = request.META['HTTP_AUTHORIZATION']
         except:
             return HttpResponse(status=401)
         encoded_credentials = auth_header.split(' ')[1]
         decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8").split(':')
         username = decoded_credentials[0]
         password = decoded_credentials[1]
         feed_bot = authenticate(username=username, password=password)
         if(feed_bot):
             try:
                 conn = pyodbc.connect(sql_con_string)
             except:
                 return HttpResponse("Failed to connect to database",content_type="text/plain")
             cursor = conn.cursor()
             data=request.query_params
             callsid=data['CallSid']
             print(callsid)
             cursor.execute("SELECT URL FROM PBCROMA.MTX.VOICEURLDATA (nolock) WHERE callsid='"+callsid+"';")
             t=cursor.fetchone()
             if t==None:
                 return HttpResponse("No data found in the database for given sid "+callsid,content_type="text/plain")
             return HttpResponse(t[0], content_type='text/plain')
         return HttpResponse(status=401)

@api_view(['GET'])
def saveExotelResponse(request):
         try:
             auth_header = request.META['HTTP_AUTHORIZATION']
         except:
             return HttpResponse(status=401)
         encoded_credentials = auth_header.split(' ')[1]
         decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8").split(':')
         username = decoded_credentials[0]
         password = decoded_credentials[1]
         feed_bot = authenticate(username=username, password=password)
         if(feed_bot):
             try:
                 data=request.query_params
                 callsid=data['CallSid']
                 DialCallDuration=data['DialCallDuration']
                 EndTime=data['EndTime']
                 CallType=data['CallType']
                 flow_id=data['flow_id']
                 RecordingUrl=data['RecordingUrl']
                 digits=data['digits']
                 CurrentTime=data['CurrentTime']
             except:
                 return HttpResponse(status=400)

             EndTime=urllib.unquote(EndTime)
             digits=urllib.unquote(digits)
             digits=digits.replace("\"","")
             CurrentTime=urllib.unquote(CurrentTime)   
               
             conn = pyodbc.connect(sql_con_string)
             cursor = conn.cursor()

             cursor.execute("SELECT * FROM PBCROMA.MTX.VOICEURLDATA (nolock) WHERE callsid='"+callsid+"';")
             query_result=cursor.fetchone()
             print(query_result)

             if query_result==None:
                print("No result is found for given Sid")
                responseId=1
             else:
                print("The given sid is already present in the database")
                responseId=2
                

            saveIVRtoMatrix(leadid,responseid)



             query="INSERT INTO PBCROMA.MTX.VoiceUrlData_Response(callsid,duration,endtime,flowid,url,custresponse,currenttime,calltype) VALUES ('"+callsid+"','"+DialCallDuration+"','"+EndTime+"','"+flow_id+"','"+RecordingUrl+"','"+digits+"','"+CurrentTime+"','"+CallType+"');"
             #print(query)
             cursor.execute(query)
             conn.commit()
             return HttpResponse(status=200)
         return HttpResponse(status=401)


@api_view(['POST'])
def getfinaldetails(request):
    data=request.data
    print(data)
    callSid=data['callsid'] 
    print(callSid)
    url="https://policybazaar2:d147cbf154e05ffeca727caf197ad6db24b6f24f@twilix.exotel.in/v1/Accounts/policybazaar2/Calls/"+callSid
    print(url)
    r=requests.get(url)
    #print(r.content)

    print(r.status_code)

    if r.status_code != 200:
      return HttpResponse(status=404)


    root = ET.fromstring(r.content)
    duration=root[0][11].text
    EndTime =root[0][10].text
    #print(duration)
    #print(EndTime)
    
    EndTime=urllib.unquote(EndTime)

    conn = pyodbc.connect(sql_con_string)
    cursor = conn.cursor()
    query="INSERT INTO PBCROMA.MTX.VoiceUrlData_Response(callsid,duration,endtime) VALUES ('"+callSid+"','"+duration+"','"+EndTime+"');"
    print(query)
    cursor.execute(query)
    
    query="UPDATE MTX.VoiceUrlData SET IsActive=0 WHERE CallSId= '"+callSid+"';" 
    print(query)
    cursor.execute(query)

    conn.commit()
    
    return HttpResponse(status=200)

@api_view(['POST'])
def hardcopyrecievalIVR(request):
    data=request.data
    try:
        leadId=data["leadid"]
        #customerId=data["customerId"]        
        mobileno=data["mobileno"]
    except:
        return HttpResponse(status=400)    
    sid=give_a_call(mobileno,"HCR")  
    print("got sid")

    save_res(leadId,'0','','',mobileno,'',sid)   
    return Response(status=status.HTTP_200_OK)    




def saveIVRtoMatrix(leadId,responseId):
   matrix_config=collection.find_one({"type":"matrixconfig"})
   url=matrix_config["url"]
   Authorization=matrix_config["authorization"]
   print(url)
   print(Authorization)
   
   headers = {
               "Authorization":Authorization,
               "Content-Type": "application/json"
   }
   print(headers)

   r=requests.post(url, headers=headers, data=json.dumps({"LeadId":8551,"responseId":2}))

   print(r.content)
   return HttpResponse(r.content, content_type='application/json')
