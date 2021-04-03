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


# Definir constantes
url = 'https://spreadsheets.google.com/feeds/list/1IJBDu8dRGLkBgX72sRWKY6R9GfefsaDCXBd3Dz9PZNs/14/public/values'

## Variáveis
full_cmd_arguments = sys.argv
argument_list = full_cmd_arguments[1:]
short_options = "t:n:"
long_options = ["token", "nome="]


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


def download_arquivo(url,pasta_de_download='.'):
    nome_do_arquivo = url.rsplit('/', 1)[-1]
    caminho = os.path.join(pasta_de_download, nome_do_arquivo)
    try:
        if not os.path.isfile(caminho):
            arquivo_stream = requests.get(url, stream=True)
            with open(caminho, 'wb') as local_file:
                for data in arquivo_stream:
                    local_file.write(data)
    except:
        print('Não foi possível salvar o arquivo na url {}'.format(url))


# In[7]:


def procura_nome_pdfgrep(nome, pasta='.'):
    resultado_da_busca = subprocess.getoutput('pdfgrep -i "{}" {}/*.pdf 2> /dev/null'.format(nome, pasta))
    return resultado_da_busca

def ajuda():
    print("uso: {} -n <NOME_A_SER_BUSCADO> -t <TOKEN_PUSHBULLET>".format(sys.argv[0]))
# In[8]:


criar_pasta_de_download(pasta_de_download)


# In[9]:


lista_de_links=scrape_lista_de_pdf(url)
for link in lista_de_links:
    download_arquivo(link, pasta_de_download)


# Busca usando pdfgrep

# In[11]:

try:
    arguments, values = getopt.getopt(argument_list, short_options, long_options)
except getopt.error as err:
    # Output error, and return with an error code
    ajuda()
    print (str(err))
    sys.exit(2)

if len(argument_list) != 4 :
    ajuda()
    sys.exit(2)


# Evaluate given options
for current_argument, current_value in arguments:
    if current_argument in ("-t", "--token"):
        pushbullet_token = current_value
    elif current_argument in ("-n", "--nome"):
        nome = current_value

resultado = procura_nome_pdfgrep(nome, pasta_de_download)
pb = Pushbullet(pushbullet_token)

if resultado != "":
    titulo = "Encontrado agendamento para {}".format(nome)
    push = pb.push_note(titulo, resultado)
    print('Mensagem enviada para pushbullet')
    print("Encontrado agendamento para {}: {}".format(nome,resultado))
else:
    print ("Não foi encontrado agendamento para {}".format(nome))
