# Machine Learning with web service
Access Machine Learning models via Web Service
This is the first attempt to deploy the ML algorithm and use it as a web service.

I followed the following link for reference, but don't just copy and paste the code; there are so many things you can learn if you set aside some time.
<a href = "https://www.deploymachinelearning.com/"> Tutorial Link </a>

This project's operations are as follows: 
1. Integration of git with your project
2. After performing preporcessing on your raw data, build and train two ML models using the Sklearn library.
3. Use Joblib to create a web service in the Django Rest Framework.
4. Run test cases to validate your implementation.
5. Run an A/B test to determine which ML model is working for your current dataset, and then change the model's status from testing to production.
6. Also, used the docker and created the containers but never used it.

Docker commands to generate image and use on another machine
To build docker images please run:

sudo docker-compose build
To start the docker images please run:

sudo docker-compose up
You should be able to see the running server at the address:

http://0.0.0.0:8000/api/v1/



I used the pipreqs package to generate the requirement.txt file, and you can simply run the pipreqs command to generate the requirement.txt file automatically.
