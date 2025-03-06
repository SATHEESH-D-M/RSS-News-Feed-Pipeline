# ASSIGNMENT - 4 
### (Dockerization of RSS feed collection and database storage microservices)
- Name : Satheesh D M

- Roll : MA24M023
## File Organization
```bash
ASSIGNMENT-4
├── DB                          # (Solution to Task 1) 
│   ├── dockerfile.myPGSQL      
│   ├── init_db.sh              
│   └── postgres_data           
├── RSS                         # (Solution to Task 2)
│   ├── dockerfile.RssFeed      
│   ├── feed_collector.py        
│   └── requirements.txt        
└── docker-compose.yml          # (Solution to Task 3)
```
- Attempted for all 50 points of this assignment - 4.
## Comments 

- Postgres DB image is used in this assignment.

- Both the services (db & feed_collection) have their own seperate dockerfile.

- The services are totally independent of eachother.
- The respective images can be built using these dockerfiles. To do so, navigate into DB or RSS folders then,

```bash
docker build -t <image-tag-name> -f <custom-dockerfile-name> .
```
- Most used docker commands (build, run, start, stop, rm, rmi) worked as expected for these images/containers. 
- Decent amount of logging/debugging print statements are included. So accessing log files should be helpful while debugging.   

```bash
docker logs <container-name-or-container-id>
```

## Environment variables (exhaustive list)
- Posstgres database container (Task - 1): 

(in yml format - examples)

```yml
POSTGRES_DB: news_db
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
```

- Feed collector container (Task - 2):

(in yml format - examples)

```yml
# DB connection configurations
POSTGRES_DB: news_db
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
POSTGRES_HOST: custom_postgres   
POSTGRES_PORT: 5432
# Feed parsing configurations
RSS_FEED_URL: https://www.thehindu.com/feeder/default.rss
TITLE_PATH: title
TIMESTAMP_PATH: published
WEBLINK_PATH: link
IMAGE_PATH: media_content
IMAGE_URL_PATH: url
SUMMARY_PATH: summary
POLL_INTERVAL: 600 # in seconds
```

- composing both the services (Task - 3):
    - Refer to "docker-compose.yml" (all of the above).

#### Note :
- Environment variables are defined at all the levels throughout this assignment.
    - @ docker-compose level, 
    - @ dockerfile level,
    - @ the helper script level. (feed_collector.py)

- All ENV variables have default fall back values. If not provided at the time of individual build they fall back to the values defined in the respective dockerfile.

- "feed_collector.py" can also be used for local implementation rather than as a dockerised implemention without changing the file logic. This can be achieved through ENV variable configuration itself during the time of local implementation.
## Volume mounting
- For the stored data to be persistent across container instances. the following volume is mounted.

(in yml format)
```yml
volumes: ./DB/postgres_data:/var/lib/postgresql/data
```

## Port mapping
By default both the task builds exposes ports for connectivity.

- DB build exposes port 5432 of the docker container.
- Feed collector build exposes port 8000 of the docker container.

## Individual build & run examples
- Task - 1:

```bash
# To build
docker build -t custom_postgres -f dockerfile.myPGSQL .
# To run
docker run -d \
  --name my_postgres \
  --network my_network \
  -e POSTGRES_DB=news_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -p 5432:5432 \
  -v ./DB/postgres_data:/var/lib/postgresql/data \
  custom_postgres

```
- Task - 2:
```bash
# To build
docker build -t feeds1 -f dockerfile.RssFeed .
# To run
docker run -d \
  --name feed_collector \
  --network my_network \
  -e POSTGRES_DB=news_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_HOST=my_postgres \
  -e POSTGRES_PORT=5432 \
  -e RSS_FEED_URL=https://www.thehindu.com/feeder/default.rss \
  -e TITLE_PATH=title \
  -e TIMESTAMP_PATH=published \
  -e IMAGE_PATH=media_content \
  -e IMAGE_URL_PATH=url \
  -e SUMMARY_PATH=summary \
  -e POLL_INTERVAL=600 \
  feeds1
```

## Compose

To get the same effect as above individual build and runs. Navigate to the ASSIGNMENT-4 folder where "docker-compose.yml" is, then do
```bash
docker-compose up
```

## Configuring ENV variables to other RSS feed providers

- To tap into other RSS feed providers other than the default ("The Hindu News"), configure the variables according to the logic of the "feed_collector.py" script and the other feed provider. The code excerpt used is shown here for reference.

```python
title = entry.get(TITLE_PATH, "")
publication_timestamp = entry.get(TIMESTAMP_PATH, "")
weblink = entry.get(WEBLINK_PATH, "")
image_url = entry.get(IMAGE_PATH, [{}])[0].get(IMAGE_URL_PATH, "") if entry.get(IMAGE_PATH) else ""
picture = fetch_and_encode_image(image_url)
tags = parse_tags(entry.get("tags", []))
summary = entry.get(SUMMARY_PATH, "")
```
## Helper scripts

- init_db.sh

- feed_collector.py

are the helper files. These code files are well commented. Since this assignment focus is on dockerization, the logic and flow of these files are not discussed here.