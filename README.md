# Async W-2 Intelligence & Movies API

App will accepts W-2 files and parses all form fields using Gemini, and produces document insights from extracted data. Also provides an API to search movies title and director from an external API.

Task App is built asynchronously to achieve high throughput and low latency.

## Installation Steps
_Follow the below instructions to setup the task application in any env._

### Prerequisites
#### Docker / Docker Compose Installation
* Install docker desktop / docker based on your system OS and architecture (preferably Linux).
  * Docker Desktop Installation (Windows) - https://docs.docker.com/desktop/setup/install/windows-install/
  * Docker Installation (choose your platform) - https://docs.docker.com/engine/install/
  * Docker Compose Installation - https://docs.docker.com/compose/install/

#### Setup WSL (only for windows)
* Setup wsl2 version in your Windows machine, by following the steps mentioned.
  * wsl2 Installation & Setup - https://learn.microsoft.com/en-us/windows/wsl/install

#### Install Postman
* Install Postman to trigger and verify the W2 & Movies APIs.
  * Download postman here - https://www.postman.com/downloads/

#### Git Installation
* Install GIT in your local, if required or download the source code from GIT
  * Download GIT - https://git-scm.com/downloads

#### Clone Project
* Ignore this step if you are downloading source code directly from GIT.
* Repo link - #
```bash
git clone 
cd technicaltask
# make sure branch is in master and up to date
git checkout master
git pull origin master
```

#### Launch Task Project
* Make Sure to add the .env file in the repo path with following env variables based on the environment.
```bash
REDIS_HOST=localhost
MYSQL_ROOT_PASSWORD=root_pwd
MYSQL_DATABASE=task_db
MYSQL_USER=your_user
MYSQL_PASSWORD=your_pwd
```
* Ensue docker & compose is up and running.
```bash
docker ps -a
docker-compose -f docker-compose.yml ps -a
```
* Build Task application
```bash
docker-compose -f docker-compose.yml build --no-cache
```
* Start all the containers and verify its up and running
```bash
docker-compose -f docker-compose.yml up -d
# check application status
docker-compose -f docker-compose.yml ps -a 
```

#### Create User and DB as per your requirements.
* Login to mysql, Refer user, password and host in env
```bash
docker-compose -f docker-compose.yml exec db bash
psql -U <username> -h <host_name> -d <db_name> 
```
* Create additional user & DB if required.
* exit the bash with (exit) command

#### Apply initial migrations
* apply initial migrations with the following migrate command
```bash
docker-compose -f docker-compose.yml exec app bash
# migration command
python manage.py migrate
```

#### Test application with the postman collection included.
* Included the postman collection (task.postman_collection.json).
* Import the collection in the postman app and try to create events and register attendees.

#### Task routes (local).
* Ping - http://localhost:8000/api/ping/
* POST W2 Forms - http://localhost:8000/api/w2
* Get W2 Status - http://localhost:8000/api/w2/{job_id}
* Movies Search - http://localhost:8000/api/movies?q={keyword}&page={n}

#### To generate migration file.
* Any changes in db structure, generate migration files with alembic
  (not required as initial migrations are already done)
* Follow upgrade command mentioned above to reflect the changes in db
```bash
docker-compose -f docker-compose.yml exec app bash 
python manage.py makemigrations
```
------
### Hooray! You've Made it 😅