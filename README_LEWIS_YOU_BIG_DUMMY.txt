TO START AGAIN:

Activate a virtual environment:
	python3 -m venv venv
	source venv/bin/activate


Pip a buncha stuff (or maybe import requirements.txt? unclear):
	pip install Django gunicorn whitenoise   
	pip install requests


whos_playing is the project, and theyre_playing is the app. All visual code, all spotyify processing, everytying really lives on theyre_playing.

To make things work run the project (python manage.py runserver) and navigate to the app in the web browser (http://localhost:8000/theyre_playing/).

Right now the HTML is in theyre_playing/templates/index.html and the logic is in theyre_playing/views.py

To deploy to Koyeb, push to git:
	git add .
	git commit -m "<COMMIT COMMENT>"
	git push -u origin main

Then on Koyeb website find our whos-playing service and re-deploy it. Can access at https://basic-juliette-lewisv-07ce2c68.koyeb.app/theyre_playing/
	^ (but maybe we need sub-directories now for theyre_playing?)