import requests
import os

# Endpoint URL
url = "http://localhost:5002/accidentcheckmulti"

# List of image filenames to test
image_files = [
    '14c3cdd4-9de6-4fce-8c17-494ca036dd04.jpeg',
    '819b55f8-5912-4da7-a5b4-898e28378e35.jpeg',
    'c89c6cac-f51a-45cf-bfcd-b8d7f7a1c521.jpeg',
    'f17a02b1-0c40-4eb5-ac50-b6012cb09342.jpeg'
]

# Base path to your test images
base_path = "C:\\WiseDrive\\python_code\\Car-damage-detection-_main\\output\\accidentcheck\\"

# Prepare multiple image files for upload
files = [('images', open(os.path.join(base_path, fname), 'rb')) for fname in image_files]

# Send POST request
response = requests.post(url, files=files)

if response.status_code == 200:
    data = response.json()

    print("✅ Response received")
    print("📝 Summary:", data.get("summary"))
    print("🧠 Text Summary:\n", data.get("text_summary"))

    # Image is expected to be null
    if data.get("image") is None:
        print("📷 No image returned (as expected)")
    else:
        print("⚠️ Unexpected image data received")

else:
    print("❌ Error:", response.status_code)
    print(response.text)