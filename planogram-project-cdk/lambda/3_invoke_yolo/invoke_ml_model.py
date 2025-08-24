import boto3, cv2, time, base64, json, numpy


def invoke_YOLO(image_bytes):

    infer_start_time = time.time()

    # Read the image into a numpy array
    nparr = numpy.frombuffer(image_bytes, numpy.uint8)

    # Read the image into a numpy array
    original_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Convert the array into jpeg
    jpeg = cv2.imencode(".jpg", original_image)[1]

    # Serialize the jpg using base 64
    img_payload = base64.b64encode(jpeg).decode("utf-8")

    conf = 0.52
    iou = 0.75
    payload = f"{img_payload}|{conf}|{iou}"

    # print(payload)

    print(f"Test payload size: {len(payload)} bytes")

    runtime = boto3.client("runtime.sagemaker")
    response = runtime.invoke_endpoint(
        EndpointName="yolo11x-endpoint-20250813-094151",
        ContentType="text/csv",
        Body=payload,
    )

    infer_end_time = time.time()
    print(f"Inference Time = {infer_end_time - infer_start_time:0.4f} seconds")

    response_body = response["Body"].read()
    result = json.loads(response_body.decode("ascii"))

    return result["boxes"], original_image
