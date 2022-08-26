import re
import os
import wmi
import pyperclip as cp
import requests
from urllib.parse import urlparse
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
from colorama import init,Fore, Back, Style


def getURL():
    cmd = input("\nEnter MSP url: ")
    if cmd == "exit":
        exit()
    print("\n")
    return cmd

def getDomainName(url):
    domain = urlparse(url).netloc
    print(Fore.CYAN+"Domain: "+Fore.WHITE,domain, "\n")
    return domain
    
    

def getEnvironment(domain):
    if re.match(r'.*(prod[\.]{1}apps[\.]{1}msa[\.]{1}libgbl[\.]{1}biz).*',domain):
        env = "Prod"
        print(Fore.CYAN+"Environment: "+Fore.WHITE,env, "\n")
        return env
    elif re.match(r'.*(apps[\.]{1}npd[\.]{1}msa[\.]{1}libgbl[\.]{1}biz).*',domain):    
        env = "Non Prod"
        print(Fore.CYAN+"Environment: "+Fore.WHITE,env, "\n")
        return env
    elif re.match(r'.*(prod[\.]{1}apps[\.]{1}cluster[\-]{1}p001[\.]{1}msp[\.]{1}upc[\.]{1}biz).*',domain):
        env = "Prod (AWS)"
        print(Fore.CYAN+"Environment: "+Fore.WHITE,env, "\n")
        return env
    elif re.match(r'.*(apps[\.]{1}cluster[\-]{1}np001[\.]{1}msp[\.]{1}upc[\.]{1}biz).*',domain):
        env = "Non Prod (AWS)"
        print(Fore.CYAN+"Environment: "+Fore.WHITE,env, "\n")
        return env   
    else:
        return None 


def searchHost(domainName,env):
    file1 = open("C:\Windows\System32\drivers\etc\hosts", "r")
    contents = file1.readlines()
    file1.close()
    if env == 'Prod':
        dnsEntry = "172.23.29.223"+ '   '+ domainName + '\n'
        print(Fore.CYAN+"DNS Entry: "+Fore.WHITE,dnsEntry)
    if env == 'Non Prod':
        dnsEntry = "172.23.29.221"+ '   '+ domainName + '\n' 
        print(Fore.CYAN+"DNS Entry: "+Fore.WHITE,dnsEntry)
    if dnsEntry in contents:
        searchResponse = {"availability" : True,
                          "dnsEntry" : dnsEntry }
        return searchResponse
    else:
        searchResponse = {"availability" : False,
                          "dnsEntry" : dnsEntry }
        return searchResponse

def updateHost(dnsEntry,env):
    file1 = open("C:\Windows\System32\drivers\etc\hosts", "r")
    contents = file1.readlines()
    file1.close()
    if env == "Prod":
        try:
            index = contents.index('##MSP PROD##\n')
        except ValueError:
            contents.insert(len(contents)+1,'##MSP PROD##\n')
            index = contents.index('##MSP PROD##\n')
    
        contents.insert(index + 1,dnsEntry)
        with open("C:\Windows\System32\drivers\etc\hosts", "w") as hostfile:
            hostfile.write("".join(str(item) for item in contents))
        hostfile.close()
    else:
        try:
            index = contents.index('###MSP NPD###\n')
        except ValueError:
            contents.insert(len(contents)+1,'###MSP NPD###\n')
            index = contents.index('###MSP NPD###\n')
        
        contents.insert(index + 1,dnsEntry)
        with open("C:\Windows\System32\drivers\etc\hosts", "w") as hostfile:
            hostfile.write("".join(contents))
        hostfile.close()


#---> Native Curl Invoking
# def mspTrigger(url):
#     cmd = 'curl -v -k -X GET "{0}" -H "MWMD-requestTimestamp: 123" -H "MWMD-activityName: 123" -H "MWMD-conversationID: 123" -H "MWMD-requestID: 123"'.format(url)
#     res = os.popen(cmd).read()
#     cp.copy(res) #(Shift+Alt+F)
#     print(res)
#     #print(os.system(cmd))

def mspTrigger(url):
    headers = {'MWMD-requestTimestamp': 'H1', 'MWMD-activityName' : 'H2', 'MWMD-conversationID': 'H3', 'MWMD-requestID': 'H4'}
    ch = input("Any additional header parameter?(y/n) ")
    while( ch !='n'):
        key,value = input("key:value ").split(':')
        headers.update({key:value})
        ch = input("Any additional header parameter?(y/n)") 
    disable_warnings(InsecureRequestWarning)     
    res = requests.get(url,headers = headers,verify=False)
    print(Fore.CYAN+"\nStatus code: "+Fore.WHITE,Fore.YELLOW+str(res.status_code)+Fore.WHITE)
    print(Fore.CYAN+"\nResponse: "+Fore.WHITE,Fore.GREEN + res.text + Fore.WHITE)
    ch = input("\nDo you want to save the response?(y/n) ")
    if(ch == 'y'):
        with open("./response.json", "w") as responseFile:
            responseFile.write("".join(res.text))
        responseFile.close()
        print("Response saved in response.json")
    else:
        cp.copy(res.text)
        print("Response copied to clipboard")

def checkWorkstation():
    sys = wmi.WMI()   
    currentSystem = sys.Win32_ComputerSystem()[0]
    #print(f"Manufacturer: {currentSystem.Manufacturer}")
    return currentSystem


def localMain():
    while(True):
        url = getURL()
        domainName = getDomainName(url)
        env = getEnvironment(domainName)
        if domainName == '' or env == None:
            print(Fore.RED+"Invalid MSP url\n"+Fore.WHITE)
            continue
        if env == "Prod (AWS)" or env == "Non Prod (AWS)":
            print(Fore.RED+"Trigger this API using VDI since AWS url is not accessable in Infosys machine\n"+Fore.WHITE)
            continue
        if env == 'Prod' or env == 'Non Prod':    
            res = searchHost(domainName,env)
            if res.get("availability"):
                print(Fore.CYAN+"Host File: "+Fore.WHITE+"Not Modified\n")
            else:
                updateHost(res.get("dnsEntry"),env)
                print(Fore.CYAN+"Host File: "+Fore.WHITE+"Modified\n")
            try:
                mspTrigger(url)
            except requests.exceptions.ConnectionError:
                print(Fore.RED+"Unable to establish connection\n"+Fore.WHITE)



def remoteMain():
    while(True):
        url = getURL()
        domainName = getDomainName(url)
        env = getEnvironment(domainName)
        if domainName == '' or env == None:
            print(Fore.RED+"Invalid MSP url\n"+Fore.WHITE)
            continue
        if env == 'Prod' or env == 'Non Prod':
            print(Fore.RED+"Trigger this API using Infosys machine since On-prem is not accessable in VDI\n"+Fore.WHITE)
        if env == "Prod (AWS)" or env == "Non Prod (AWS)":
            try:
                mspTrigger(url)
            except requests.exceptions.ProxyError:
                print(Fore.RED+"Unable to establish connection."+Fore.WHITE)      


# if __name__ == "__main__":
#     while(True):
#         url = getURL()
#         domainName = getDomainName(url)
#         env = getEnvironment(domainName)
#         if domainName == '' or env == None:
#             print("Invalid MSP url\n")
#             continue
#         if env == 'Prod' or env == 'Non Prod':    
#             res = searchHost(domainName,env)
#             if res.get("availability"):
#                 print("Host File: Not Modified\n")
#             else:
#                 updateHost(res.get("dnsEntry"),env)
#                 print("Host File: Modified\n")
#             try:
#                 mspTrigger(url)
#             except requests.exceptions.ConnectionError:
#                 print("Unable to establish connection. Please try in VDI")
#         else:
#              try:
#                 mspTrigger(url)
#              except requests.exceptions.ProxyError:
#                 print("Unable to establish connection. Please try in local machine")
        

if __name__ == "__main__":
    init()
    a="""
       _    _    _____  _____
      / \  / \  / ____||  __ \      
     / . \/ . \ \____ \|  __ /
    / / \  / \ \ ____) | | 
   /_/   \/   \_\_____/|_|
 _        _
| |_  _ _(_) __ _  __ _ ____  _ _
|  _|| `_| |/ _` |/ _` |  _ \| `_|
| |_ | | | | (_) | (_) |  __/| |  
 \__/|_| |_|\__  |\__  |\___||_|
============|__ / |__ /===========
"""

    print(Fore.GREEN+a+Fore.WHITE)
    currrentSys = checkWorkstation()
    if currrentSys.Manufacturer == 'VMware, Inc.':
        print( Fore.BLUE+"Running in remote mode\n"+Fore.WHITE)
        remoteMain()
    else:
        print( Fore.BLUE+"Running in local mode\n"+Fore.WHITE)
        localMain()
