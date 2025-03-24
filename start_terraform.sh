# First time setup
terraform init
terraform plan -var="project_id=berliner-luft-dez"
terraform apply -var="project_id=berliner-luft-dez"


# Daily/hourly execution
python src/pipeline.py