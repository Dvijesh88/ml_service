# ml_service
Machine Learning via Web Service
This is the first attempt to deploy the ML algorithm and use it as a web service.

I followed the following link for reference, but don't just copy and paste the code; there are so many things you can learn if you set aside some time.
a href = "https://www.deploymachinelearning.com/"> a>Tutorial Link

This project's operations are as follows: 
1. Integration of git with your project
2. After performing preporcessing on your raw data, build and train two ML models using the Sklearn library.
3. Use Joblib to create a web service in the Django Rest Framework.
4. Run test cases to validate your implementation.
5. Run an A/B test to determine which ML model is working for your current dataset, and then change the model's status from testing to production.

I used the pipreqs package to generate the requirement.txt file, and you can simply run the pipreqs command to generate the requirement.txt file automatically.
