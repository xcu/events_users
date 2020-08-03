# events web application

## Author
César Muñoz.

## Python version
This project uses Python 3.8.

## How to deploy the project
After cloning the repo in your local machine you just need a couple of additional steps.
There is a **docker-compose.yml** file, which will deploy the three required containers:

 - **web**, which is the actual Django container. This one is built using the provided **Dockerfile**.
 - **db**, which is the Postgresql instance.
 - **cache**, which is a Redis instance used to cache the event list.
 
To deploy the aforementioned containers docker-compose needs to be installed. If needed, instructions to install it can be found [here](https://docs.docker.com/compose/install/).
After that, to run the cluster, execute the following command

    docker-compose up

This will deploy the cluster and run Django. A bash script has been included to create the appropriate tables in Postgres. You can execute it by running

    sh deploy.sh

Now you are all set! Try this URL to create a user in the application

    http://localhost:8085/accounts/sign_up/

If you want to run the tests, do 

    docker-compose exec web /root/.poetry/bin/poetry run python manage.py test events_users

## Useful URLs
User sign up

    http://localhost:8085/accounts/sign_up/

User log in

    http://localhost:8085/accounts/login/

User logout

    http://localhost:8085/accounts/logout/
Event creation

    http://localhost:8085/events/

Event list

    http://localhost:8085/events/all

## Notes about the implementation

### Poetry
 - Poetry has been used to handle dependencies and run a virtualenv.
 - While this is a very useful tool in the development cycle, if the **web** container was to be used in production I would probably package the container a bit differently, without Poetry, installing the requirements with pip on top of a Python 3.X container.

### Redis
 - There is a caching mechanism to show the events when a user is logged in. This way, if thousands of users request the same list of events over and over the Postgres DB will not be flooded with requests.
 - If the cache server is not available then Postgres will be queried.
 - The caching system used has been kept simple on purpose, as it can be complicated as much as desired. For instance, if the **cache** container goes down and operations are made then, when the container is back up, users will not see those changes.
 - To cater for that we would need a system that updates Redis if it goes down. Probably a heartbeat system or something like that.
 - In a live system, with a properly sized cache, it would be more unlikely to suffer a complete failure in the caching system, but of course it would be something that would need to be looked into.

### REST API
 - Since the focus of this project is on the backend no Javascript has been included. Hence, forms do not make use of PUT or DELETE requests. That results in an API which may not be as RESTful as a different approach with more JS.
 - However, if we had a bigger focus on the frontend we would likely do things like issuing PUT requests to update Event objects and such.