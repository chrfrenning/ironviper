FROM python:2
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN curl https://imagemagick.org/download/binaries/magick > ./magick
RUN chmod +x ./magick
COPY converter.py ./
CMD [ "python", "./converter.py" ]