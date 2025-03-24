# steps taken for development

## get permissions
sudo chown -R $(whoami) ~/.config/  
## create new folder
mkdir ~/.config/gcloud  
## grant permissions
sudo chown -R $(whoami) ~/.config/gcloud  

## initialize google cloud
gcloud init

## create new project with unique name
gcloud create berliner-luft-dez

## set credentials
gcloud auth application-default login



#### start project

##### prompting chatgpt and deepseek on how to start the project:

```
I am starting a data engineering project where I get some data from umweltbundesamt API and I want to get the data into a database in the cloud. 
It's hourly measurements of different polluters in the air, so not huge data, but it is planned to be updated every day or even every hour. 
My plan was to download the data as JSON and then upload it to google cloud bucket and then transfer it to a database (bigquery?). then, using a web hosted dashboard or some google tool, I would create a dashboard of the data telling people "how bad the current air quality in Berlin is", for example.
Is that plan a good idea, or is it overkill? Are there ways to make things more simple, e.g. by directly transferring the data from the API into a database (which is not bigquery)? 


I am doing the project for a course as a final project, so it would be nice if i would score high in the project and learn a lot doing it, but i also dont want to use unnecessary overhead technology ("Mit Kanonen auf Spatzen schießen").

This is the project description / scoring criteria:

(...)

Please guide me on how I should best approach my project and which technologies you advise me to use.
```

#### making a plan

**Phase 1: Core Solution (Week 1-2)**
1. Basic Infrastructure
    * Terraform for GCS + BigQuery
    * Cloud Function for daily API ingestion
2. Data Flow
    * API -> GCS (JSON) -> BigQuery (raw table)
    * Native SQL transformations
3. Dashboard
    * Looker Studio with 2 tiles
    * Basic time-series and distribution charts

**Phase 2: Advanced Features (Week 3-4)**
1. Workflow Orchestration
    * Migrate from Cloud Functions to Cloud Composer
    * Implement Airflow DAG with proper error handling
2. Data Quality
    * Add dbt for transformations
    * Implement data quality tests
3. Dashboard Enhancements
    * Add historical trends
    * Implement alert thresholds


Key Milestones
1. End of Week 1: Working data pipeline (API -> GCS -> BQ)
2. End of Week 2: Functional dashboard with 2 tiles
3. End of Week 3: Airflow DAG operational
4. End of Week 4: dbt transformations complete

**Fallback Strategy**
If time runs short:
* Document planned improvements
* Include architecture diagrams for future state
* Show working core solution