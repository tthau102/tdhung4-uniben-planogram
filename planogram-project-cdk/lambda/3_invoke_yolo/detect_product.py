import boto3, base64, json

SHELF_LABEL = "shelf"
DRINK_LABELS = ["boncha", "joco", "abben"]

CLASS_MAP = {
    0: "abben",
    1: "boncha",
    2: "joco",
    3: "shelf"
}

BOTTLE_CLASS_IDS = {0, 1, 2}

def extract_shelves_and_bottles(detections):
    print("Extracting shelves and bottles from detection results...")
    shelves = []
    bottles = []
    for item in detections:
        if not isinstance(item, list) or len(item) < 6:
            continue
        x1, y1, x2, y2, conf, class_id = item
        cls_id = int(class_id)
        label = CLASS_MAP.get(class_id)
        bbox = [x1, y1, x2, y2]

        if label == SHELF_LABEL:
            shelves.append(bbox)
        elif class_id in BOTTLE_CLASS_IDS:
            bottles.append({'type': label, 'bbox': bbox})
        else:
            continue  # ignore all other non-bottle objects

    # print(f"Shelves detected: {len(shelves)}, Bottles detected: {len(bottles)}")
    print("Extracting done!")
    return shelves, bottles


def organize_bottles_by_shelf(shelves, bottles):
    print("Organizing bottles by shelf...")
    sorted_shelves = sorted(shelves, key=lambda b: b[3], reverse=True)
    results = []
    for idx, shelf_box in enumerate(sorted_shelves):
        shelf_number = idx + 1
        shelf_x1, shelf_y1, shelf_x2, shelf_y2 = shelf_box
        drink_count = {label: 0 for label in DRINK_LABELS}
        for bottle in bottles:
            bx1, by1, bx2, by2 = bottle['bbox']
            center_x = (bx1 + bx2) / 2
            center_y = (by1 + by2) / 2
            if shelf_x1 <= center_x <= shelf_x2 and shelf_y1 <= center_y <= shelf_y2:
                drink_count[bottle['type']] += 1
        results.append({
            'shelf_number': shelf_number,
            'drinks': drink_count
        })
    # print("Shelf analysis:", json.dumps({'shelves': results}, indent=2, ensure_ascii=False))
    print("Organizing done!")
    return {'shelves': results}