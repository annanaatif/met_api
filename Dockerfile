FROM python:3.12.10

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]




# steps to run the docker container-
#     add .env file in the root directory
#     then add required credentials in the .env file
#     create docker-compose.yml file in the root directory
#     then run the command docker-compose up --build
#     then run the command docker-compose up -d
#     then run the command docker-compose exec web python manage.py migrate
#     then run the command docker-compose exec web python manage.py fetch_met
#     then run the command docker-compose exec web python manage.py runserver
#     then run the command docker-compose down