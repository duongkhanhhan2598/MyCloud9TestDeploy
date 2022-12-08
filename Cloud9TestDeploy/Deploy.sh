export PROJECT_ID=MySample1
export AWS_ACCOUNT=096163215653
export AWS_REGION=${AWS_REGION:-"ap-northeast-1"}

export S3_BUCKET=${PROJECT_ID}-${AWS_ACCOUNT}-${AWS_REGION}
## aws s3api create-bucket --bucket ${S3_BUCKET} --region ${AWS_REGION} --create-bucket-configuration LocationConstraint=${AWS_REGION} || true
aws s3api create-bucket --bucket ${S3_BUCKET} --region ${AWS_REGION} --create-bucket-configuration LocationConstraint=${AWS_REGION}
aws s3api put-bucket-versioning --bucket ${S3_BUCKET} --versioning-configuration Status=Enabled

## Build the Lib
sam build --use-container --template-file template.yaml

## Deploying the Application
sam deploy --stack-name ${PROJECT_ID}                   \
           --template-file .aws-sam/build/template.yaml       \
           --s3-bucket ${S3_BUCKET} --s3-prefix ${PROJECT_ID}                        \
           --region ${AWS_REGION} --confirm-changeset --no-fail-on-empty-changeset   \
           --capabilities CAPABILITY_NAMED_IAM          \
           --config-file samconfig.toml                 \
           --no-confirm-changeset                       \
           --tags \
              Project=${PROJECT_ID}