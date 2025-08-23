import cv2

def draw_boxes_and_upload_to_S3(s3, bucket, imageName, detections, original_image):
    CLASS_COLORS = {
        0: (0,255,0),
        1: (255,0,0),
        2: (0,0,255),
        3: (0,0,0),
    }

    CLASS_NAMES = {
        0: "abben",
        1: "boncha",
        2: "joco",
        3: "shelf",
    }

    for box in detections:
        x1, y1, x2, y2, confidence, classID = box
        color = CLASS_COLORS.get(int(classID), (255,255,255))

        cv2.rectangle(original_image, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness=2)

        conf_label = f'{confidence:.2f}'
        cv2.putText(original_image, conf_label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


    img_encoded = cv2.imencode('.jpg', original_image)[1]
    img_bytes = img_encoded.tobytes()

    if imageName.count('/') == 0:
        fileName=imageName
    elif imageName.count('/') == 1:
        # If there is only one '/', return only the number
        fileName=imageName.split('/')[1].split('.')[0]
    else:
        # If there are more than one '/', return everything after the first '/'
        fileName='/'.join(imageName.split('/')[1:]).split('.')[0]

    fileKey=f"annotated-images/{fileName}_annotated.jpg"
    s3.put_object(
        Bucket="uniben-planogram-test",
        Key=fileKey,
        Body=img_bytes,
        ContentType='image/jpeg'
    )
    print(f"{fileKey} has been uploaded to S3.")
    return fileKey
