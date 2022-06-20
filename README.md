# ml_service
Machine Learning with Web service
This is first attempt to deploy the ML algorithm and use them as web services.

I have followed the folliwing link for the reference but dont blindly copy paste the code, there are so many things you can learn if you sepnd some amount of time.
<a href = "https://www.deploymachinelearning.com/"> Tutorial Link </a>

Operations which this project perform are:
1. Integration og git with you project
2. build and train two ML models from Sklearn library after perfoming preporcessing on your raw data
3. Use Joblib to create web service in Django rest framework
4. Perform test cases to validate the your implementation
5. Perform A/B test to indentify which ML model is working for your current dataset and based on that you can change the status of the model from testing to production  


To generate requirement.txt file, i have used pipreqs package and you can simply run pipreqs command to generate requirements.txt file autometically
