# gemini-api-developer-competition 

# welcome to my repo 

## i am using gemini api to classify image then use gemini api again to recommend based on classification output and your current location details and current date the best plant you can grow now  to help our planet and solve global warming and absorb max carbon amount.

## to get flask app

### - run below docker image 
```sh
docker run -p 5000:5000 docker.io/elhalag93/gemeini-plant-recommendation
```
### then access http://127.0.0.1:5000

### upload soil image then you will be redirected to recommended plants you can grow to help our planet


### - or  you can clone  the repo and run the flask app
```sh
git clone https://github.com/elhalag93/gemini-api-developer-competition-

cd gemini-api-developer-competition-

pip3.9 install Flask requests google-generativeai grpcio

python3.9 app.py
```
### then access http://127.0.0.1:5000
###        or 
### access http://<machine_ip>:5000

### - upload soil image then you will be redirected to recommended plants you can grow to help our planet


