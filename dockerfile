FROM alpine:3.13.4

RUN apk update && \
    apk add python3 py-pip libxml2-dev libxslt-dev py3-lxml pdfgrep && \
    pip install  beautifulsoup4==4.9.3 Flask==1.1.2 lxml==4.6.3 pushbullet.py==0.12.0 requests==2.25.1 httplib2==0.19.1 oauth2client==4.1.3 apiclient==1.0.4 google-api-core==1.26.3 google-api-python-client==2.1.0 google-auth==1.28.0 google-auth-httplib2==0.1.0 googleapis-common-protos==1.53.0
RUN mkdir /app/
RUN mkdir /root/.credentials
COPY agendacovid19.py /app/
VOLUME /insumos
WORKDIR /insumos
ENV email="johndoe@mail.com"
ENV nome="John Doe"
ENV credencial="John Doe"
CMD ["sh","-c","/app/agendacovid19.py -n ${nome} -m ${email}"]
