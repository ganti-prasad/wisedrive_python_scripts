import requests
import base64
import json
from datetime import datetime

# 🔧 Config
api_url = "http://localhost:5002/exterioranalysis"  # Update if hosted remotely
filename='raw1'
image_path = f"C:\\WiseDrive\\python_code\\Car-damage-detection-_main\\output\\{filename}.jpg"
output_image_path = f"C:\\WiseDrive\\python_code\\Car-damage-detection-_main\\output\\{filename}_annotated_from_api.jpg"

# ⏳ Start time
start_time = datetime.now()
print(f"🚀 Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 📤 Send image to API
with open(image_path, "rb") as f:
    files = {"image": f}
    response = requests.post(api_url, files=files)

# ⏱️ End time
end_time = datetime.now()
print(f"🏁 End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 🕒 Processing duration
duration = end_time - start_time
print(f"⏱️ Processing Time: {duration.total_seconds():.2f} seconds")


# 🧾 Handle response
if response.status_code == 200:
    data = response.json()
    print(f"data ====== {data}")
    # 🖼️ Save annotated image
    image_b64 = data["image"]
    with open(output_image_path, "wb") as f:
        f.write(base64.b64decode(image_b64))
    print(f"✅ Annotated image saved as: {output_image_path}")

    # 📊 Print summary
    print("\n📊 Summary:")
    print(json.dumps(data["summary"], indent=2))

    # 📝 Print text summary
    print("\n📝 Text Summary:")
    print(data["text_summary"])

else:
    print(f"❌ API Error: {response.status_code}")
    print(response.text)