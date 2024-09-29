FROM python:3.10
EXPOSE 5000
WORKDIR /tomato
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN apt-get update && apt-get install -y libgl1-mesa-glx
COPY . .
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "-u", "run.py"]