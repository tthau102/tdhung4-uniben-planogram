import boto3, json, os


def invoke_claude(shelfResult):
    client = boto3.client("bedrock-runtime", region_name="ap-northeast-2")
    modelId = os.getenv("INFERENCE_PROFILE")
    with open("1_system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()
    with open("2_instructions.txt", "r", encoding="utf-8") as f:
        instructions = f.read()
    with open("3_last_message.txt", "r", encoding="utf-8") as f:
        last_message = f.read()

    instructions = instructions.replace(
        "{shelf_data}", json.dumps(shelfResult, indent=2, ensure_ascii=False)
    )

    system = [
        {
            "type": "text",
            "text": system_prompt,
        }
    ]

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": instructions,
                },
                {
                    "type": "text",
                    "text": last_message,
                },
            ],
        },
    ]

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": system,
        "messages": messages,
        "max_tokens": 500,
        "top_p": 0.9,
        "top_k": 20,
        "temperature": 0,
    }

    response = client.invoke_model(
        modelId=modelId,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    model_response = json.loads(response["body"].read())
    print(model_response)
    return [model_response["usage"], model_response["content"][0]["text"]]


def invoke_nova():
    # Implement invoke to Nova
    return 1
