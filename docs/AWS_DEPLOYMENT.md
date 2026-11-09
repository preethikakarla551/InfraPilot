# AWS deployment (portfolio environment)

This deployment creates real AWS resources in `ap-south-1`: a VPC with an internet-facing application subnet, two isolated database subnets, one small EC2 host, one private single-AZ RDS MySQL database, a private ECR repository, an instance role, and one Secrets Manager secret. Terraform creates the network and database first. The API host is intentionally held back until its image has been pushed to ECR. In AWS mode, diagnostic history is stored in RDS MySQL; local mode continues to use SQLite.

The public security group accepts HTTP on port 80. Nginx exposes only `/health`; every other route, including diagnostics, history, metrics, and network checks, returns 404. There is no inbound SSH rule. Use Systems Manager Session Manager for host administration. This is a small live portfolio deployment, not a production-ready service: it has no HTTPS, high availability, automatic backups beyond the short RDS retention period, or disaster-recovery setup.

## Before provisioning

- Check AWS Billing and Cost Management. Confirm the account is still on the Free account plan and note the remaining credit and plan end date.
- Do not choose **Upgrade plan**. The Free plan has service and time limits; after it ends the account and resources can be closed unless you upgrade. Review [AWS Free Tier plans](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).
- This configuration can consume credits while EC2, RDS, ECR storage, Secrets Manager, and public IPv4 resources exist. Credits are not a spend cap. Do not apply unless you are comfortable consuming them, and destroy the stack after the portfolio demonstration.
- Create AWS credentials for Terraform using a dedicated IAM identity with only the permissions needed for this deployment. Never use or paste root-account access keys. Never share access keys, passwords, account IDs, or `.env` contents in chat.
- Terraform's local state contains sensitive values, including the database password. Keep the state file and `terraform.tfvars` on your private computer; neither should be committed. `.gitignore` excludes both.

## Phase 1: prepare and inspect

Run these commands in Ubuntu/WSL from the project directory. AWS CLI, Terraform, and Docker Desktop must be installed and available in WSL. Configure AWS credentials using your dedicated IAM identity, then check which identity Terraform will use:

```bash
aws sts get-caller-identity
```

Create `terraform/terraform.tfvars` by copying `terraform/terraform.tfvars.example`, then replace the database password with a unique value of at least 16 characters. Do not paste that password into chat. Initialize and validate the configuration:

```bash
cd /mnt/c/Users/LENOVO/Documents/InfraPilot/terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
terraform fmt -recursive
terraform init
terraform validate
```

Review the first plan before applying. With `deploy_app = false`, this phase creates the VPC, private RDS database, ECR repository, secret, and IAM role, but no application EC2 instance:

```bash
terraform plan -out=infra.tfplan
```

Check the plan counts and resource list. Stop if it proposes unrelated resources, a paid-plan upgrade, or anything you do not understand. Do not run `terraform apply` until the plan has been reviewed.

## Phase 2: create base infrastructure and publish the image

After reviewing and approving the plan, create the base resources:

```bash
terraform apply infra.tfplan
```

Build the already-tested API image and push it to the private ECR repository created by Terraform:

```bash
cd /mnt/c/Users/LENOVO/Documents/InfraPilot
docker build -t infrapilot:local .
REPO=$(terraform -chdir=terraform output -raw ecr_repository_url)
REGISTRY=${REPO%%/*}
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin "$REGISTRY"
docker tag infrapilot:local "$REPO:v1"
docker push "$REPO:v1"
```

## Phase 3: deploy and verify

Create a second plan that adds the EC2 host. The host boot script retrieves the database secret through its instance role, starts the API and Nginx containers, and checks both API health and private MySQL connectivity:

```bash
cd /mnt/c/Users/LENOVO/Documents/InfraPilot/terraform
terraform plan -var='deploy_app=true' -out=app.tfplan
```

Review the plan; it should add one EC2 host. Then apply that saved plan:

```bash
terraform apply app.tfplan
terraform output -raw public_health_url
```

Open the printed URL in a browser or use `curl`. Expected health response includes `"status":"ok"`. To inspect bootstrap progress, connect to the instance with **Systems Manager → Session Manager** in the AWS Console and run:

```bash
sudo tail -n 80 /var/log/infrapilot-bootstrap.log
sudo docker ps
```

The host checks `/database-check` during bootstrap, then writes and reads a diagnostic snapshot through `/diagnostics` and `/history` before declaring bootstrap healthy. Nginx blocks those routes from public access. To demonstrate them from an SSM session on the host, run `curl http://127.0.0.1:8000/diagnostics` and then `curl http://127.0.0.1:8000/history`. Do not open the database port to the internet.

## Tear down after the demonstration

Destroy the Terraform-managed resources when the live endpoint is no longer needed. Review the destroy plan carefully; this deletes the RDS database and its data:

```bash
cd /mnt/c/Users/LENOVO/Documents/InfraPilot/terraform
terraform destroy -var='deploy_app=true'
```

Confirm the prompt only after checking the resource list. ECR images and Secrets Manager resources are also deleted. Then check **Billing → Bills** and **Cost Explorer** for any remaining resources or delayed usage. Do not delete the local Terraform state until AWS confirms the stack is gone.
