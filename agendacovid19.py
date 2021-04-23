#!/usr/bin/env python3
# coding: utf-8

# A Prefeitura de Fortaleza-CE divulga, por meio da Secretaria Municipal da Saúde,
# as listas de agendados, cadastrados e vacinados no portal de informações da prefeitura.
#
# Este script baixa os arquivos PDF que contém a [listas de agendados](https://coronavirus.fortaleza.ce.gov.br/vacinacao.html)
# da vacina contra o COVID19 em Fortaleza/CE, procura pelo nome dado e envia o
# resultado da busca para uma conta push bullet através da sua API


from bs4 import BeautifulSoup
from flask import Flask
from pushbullet import Pushbullet

import requests
# import urllib
import os
import getopt,sys
import subprocess

import httplib2
import oauth2client
from oauth2client import client, tools, file
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery



# Definir constantes
url = 'https://spreadsheets.google.com/feeds/list/1IJBDu8dRGLkBgX72sRWKY6R9GfefsaDCXBd3Dz9PZNs/14/public/values'
SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'Agenda Covid 19 - Fortaleza'

## Variáveis
full_cmd_arguments = sys.argv
argument_list = full_cmd_arguments[1:]
short_options = "t:n:m:"
long_options = ["token", "nome=", "email="]


# In[3]:


try:
    pasta_de_download
except:
    pasta_de_download = './arquivos_baixados'


# Criar lista contendo todos os endereços dos arquivos PDF para download listados no endereço da variável url

# In[4]:


def scrape_lista_de_pdf(url):
    pdf_doc = requests.get(url).text
    soup = BeautifulSoup(pdf_doc, 'xml')
    lista_de_pdf = [ item.pdf.text for item in soup.find_all('entry') ]
    return lista_de_pdf


# Baixar os arquivos somente se já não existirem localmente

# In[5]:


def criar_pasta_de_download(pasta_de_download):
    try:
        if not os.path.isdir(pasta_de_download):
            os.mkdir(pasta_de_download)
    except OSError:
        print ("Criação do diretório de download falhou %s " % pasta_de_download)


# In[6]:

# Entrada: url de download e pasta de destino
# Saída: escreve arquivo em disco e retorna:
#   True: arquivo foi baixado
#   False: arquivo já existe
def download_arquivo(url,pasta_de_download='.'):
    nome_do_arquivo = url.rsplit('/', 1)[-1]
    caminho = os.path.join(pasta_de_download, nome_do_arquivo)
    try:
        if not os.path.isfile(caminho):
            arquivo_stream = requests.get(url, stream=True)
            with open(caminho, 'wb') as local_file:
                for data in arquivo_stream:
                    local_file.write(data)
            return True
    except:
        # print('Não foi possível salvar o arquivo na url {}'.format(url))
        return False

# In[7]:


def procura_nome_pdfgrep(nome, pasta='.', arquivos="*.pdf"):
    resultado_da_busca = []
    for arquivo in arquivos:
        resultado_da_busca.append(subprocess.getoutput('pdfgrep -i "{}" {}/{} 2> /dev/null'.format(nome, pasta,arquivo)))
    return resultado_da_busca

def ajuda():
    print("uso: {} -n <NOME_A_SER_BUSCADO> [-t <TOKEN_PUSHBULLET>] [-m emaildedestino@mail.com]".format(sys.argv[0]))

def get_credentials():
    credential_dir = './.credentials'
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-python-email-send.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def SendMessage(sender, to, subject, msgHtml, msgPlain):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    message1 = CreateMessage(sender, to, subject, msgHtml, msgPlain)
    SendMessageInternal(service, "me", message1)

def SendMessageInternal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)

def CreateMessage(sender, to, subject, msgHtml, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    msg.attach(MIMEText(msgHtml, 'html'))
    raw = base64.urlsafe_b64encode(msg.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}
    return body


def main():
    criar_pasta_de_download(pasta_de_download)
    lista_de_links=scrape_lista_de_pdf(url)
    lista_de_arquivos_baixados=[]
    for link in lista_de_links:
        if download_arquivo(link, pasta_de_download):
            arquivo_no_link = link.rsplit('/', 1)[-1]
            lista_de_arquivos_baixados.append(arquivo_no_link)
    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        # Output error, and return with an error code
        ajuda()
        print (str(err))
        sys.exit(2)

    if len(argument_list) < 4 :
        ajuda()
        sys.exit(2)

    # Evaluate given options
    for current_argument, current_value in arguments:
        if current_argument in ("-t", "--token"):
            pushbullet_token = current_value
        elif current_argument in ("-n", "--nome"):
            nome = current_value
        elif current_argument in ("-m", "--email"):
            email = current_value
    
    if len(lista_de_arquivos_baixados) > 0:
        resultado = procura_nome_pdfgrep(nome,pasta_de_download,lista_de_arquivos_baixados)
        # remover registros vazios da lista
        resultado = list(filter(None, resultado))
        print("resultado: {}".format('\n'.join(resultado)))
        if len(resultado) > 0:
            for agendamento in resultado:
                titulo = "Encontrado agendamento de vacinacão para {}".format(nome)
                if 'pushbullet_token' in globals() or 'pushbullet_token' in locals():
                    pb = Pushbullet(pushbullet_token)
                    push = pb.push_note(titulo, agendamento)
                    print('Mensagem enviada para pushbullet')
                if 'email' in globals() or 'email' in locals():
                    to = email
                    sender = "agendacovid19.fortaleza@gmail.com"
                    subject = titulo
                    msgHtml = agendamento
                    msgPlain = msgHtml
                    SendMessage(sender, to, subject, msgHtml, msgPlain)
                    print(f"Mensagem enviada para email {email}")
                print("Encontrado um novo agendamento agendamento para {}: \n {}".format(nome,agendamento))
    else:
        print ("Não foi encontrado um novo agendamento para {}".format(nome))

if __name__ == '__main__':
    main()
