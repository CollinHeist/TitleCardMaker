FROM python:3.9-alpine
RUN apk add alpine-sdk shadow

RUN adduser abuild -S
RUN addgroup abuild abuild

COPY . /home/abuild
WORKDIR /home/abuild

USER abuild

RUN abuild-keygen -a -n
RUN abuild -r