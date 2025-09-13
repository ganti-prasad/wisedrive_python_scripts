import requests
import base64
import cv2
import numpy as np

# Endpoint URL
url = "http://localhost:5002/interioranalysis"

# Path to your test image
image_file = 'PleaseTakeODOmeterPhotoWithWarningLight.jpg'
image_path = f"C:\\WiseDrive\\python_code\\Car-damage-detection-_main\\output\\ExterriorImage\\{image_file}"
output_path = f"C:\\WiseDrive\\python_code\\Car-damage-detection-_main\\output\\ExterriorImage\\output_{image_file}"
# Prepare the image file for upload
files = {
    "image": open(image_path, "rb")
}

# Send POST request
response = requests.post(url, files=files)

if response.status_code == 200:
    data = response.json()

    print("🔍 GPT Raw Output:\n", data.keys())
    # Decode base64 image
    annotated_b64 = data["image"]
    annotated_bytes = base64.b64decode(annotated_b64)
    annotated_np = np.frombuffer(annotated_bytes, np.uint8)
    annotated_img = cv2.imdecode(annotated_np, cv2.IMREAD_COLOR)

    # Save to file
    cv2.imwrite(output_path, annotated_img)
    print(f"✅ Annotated image saved to: {output_path}")
    print("📝 Inspection Report:")
    print(data.get("inspection_report"))
    print(data.get("text_summary"))
else:
    print("❌ Error:", response.status_code)
    print(response.text)
