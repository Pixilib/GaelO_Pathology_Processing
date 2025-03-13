# base image  
FROM python:3.12

# setup environment variable  
ENV DockerHOME=/home/gaelo_pathology_processing

USER root

# set work directory  
RUN mkdir -p $DockerHOME  

# where your code lives  
WORKDIR $DockerHOME

# set environment variables  
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1  

COPY ./src $DockerHOME 
COPY ./start-prod-server.sh /usr/local/bin/start-prod-server.sh
RUN chmod +x /usr/local/bin/start-prod-server.sh

COPY ./entrypoint.sh .
RUN chmod +x ./entrypoint.sh

#Install open cv dependency
RUN apt-get update -qy && apt-get install -y --no-install-recommends libgl1 libjpeg-dev libturbojpeg0-dev

# install dependencies  
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT ["/home/gaelo_pathology_processing/entrypoint.sh"]
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "900",  "--log-level", "info", "--log-file", "-", "--access-logfile", "-", "gaelo_pathology_processing.wsgi:application"]
