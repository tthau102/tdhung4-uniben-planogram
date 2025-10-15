# Planogram-Project-CDK

![diagram](diagram.png)

$env:AWS_PROFILE="uniben"

cdk init planogram --language python

.venv\Scripts\activate

cdk synth

cdk deploy --all -require-approval never
