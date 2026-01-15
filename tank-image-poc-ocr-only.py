
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import time
import os
import re
from dotenv import load_dotenv

print("Initializing detection...")

ini_time = time.time()

# Setup
# Load variables from .env
load_dotenv()

#SP account DEV
#key = os.getenv("COMPUTER_VISION_KEY_SP")
#endpoint = "https://computer-vision-sp-propane-inspection-dev-us-east.cognitiveservices.azure.com/" --DEV

key = os.getenv("COMPUTER_VISION_KEY_SP_TIM_PROD")
endpoint = "https://computer-vision-sp-tim-prod-us-east.cognitiveservices.azure.com/"

images_folder = "./Images"

# ----------------------------
# 3) Keywords list with id + word
# ----------------------------
KEYWORDS = [
    {"manufacturer": "manchester tanks", "word": "manchester"},
    {"manufacturer": "trinity", "word": "trinity"},
    {"manufacturer": "trinity", "word": "industries"},
    {"manufacturer": "quality steel", "word": "quality"},
    {"manufacturer": "quality steel", "word": "steel"},
    {"manufacturer": "american welding", "word": "american"},
    {"manufacturer": "american welding", "word": "welding"},
   # {"manufacturer": "chemitrol", "word": "chemical"}
    {"manufacturer": "lajat", "word": "lajat"},
     {"manufacturer": "lajat", "word": "leslajat"},
    {"manufacturer": "chemitrol", "word": "chemitrol"}
]

# Compile regex patterns for each keyword (whole word, case-insensitive)
keyword_patterns = [
    {"manufacturer": k["manufacturer"], "pattern": re.compile(rf"\b{re.escape(k['word'])}\b", re.IGNORECASE)}
    for k in KEYWORDS
]

# ----------------------------
# 4) Init client
# ----------------------------
client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))

# Supported image extensions
supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

# Get all image files from the folder
image_files = [f for f in os.listdir(images_folder) if f.lower().endswith(supported_extensions)]

if len(image_files) == 0:
    print(f"No images found in '{images_folder}' folder. Please add images with supported extensions ({', '.join(supported_extensions)}) and try again.")
    exit(0)

print(f"Found {len(image_files)} images to process.\n")
print("=" * 50)

results = []

for image_file in image_files:
    image_path = os.path.join(images_folder, image_file)
    
    # Run OCR on the image
    with open(image_path, "rb") as img:
        read_response = client.read_in_stream(img, raw=True)

    operation_location = read_response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # Poll until finished
    while True:
        result = client.get_read_result(operation_id)
        if result.status.lower() != "running":
            break
        time.sleep(1)

    if result.status.lower() != "succeeded":
        print(f"{image_file} -> OCR FAILED")
        results.append({"image": image_file, "manufacturer": "OCR FAILED"})
        continue

    # Search for keywords
    found_manufacturer = None

    for page in result.analyze_result.read_results:
        for line in page.lines:
            text = line.text
            for kp in keyword_patterns:
                if kp["pattern"].search(text):
                    found_manufacturer = kp["manufacturer"]
                    break
            if found_manufacturer is not None:
                break
        if found_manufacturer is not None:
            break

    if found_manufacturer is not None:
        print(f"{image_file} -> {found_manufacturer}")
        results.append({"image": image_file, "manufacturer": found_manufacturer})
    else:
        print(f"{image_file} -> No manufacturer found")
        results.append({"image": image_file, "manufacturer": "Not found"})

# ----------------------------
# 6) Summary
# ----------------------------
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
for r in results:
    print(f"{r['image']}: {r['manufacturer']}")

end_time = time.time()
exec_time = end_time - ini_time
print("\n" + "=" * 50)
print(f"Total images processed: {len(image_files)}")
print(f"Total execution time: {exec_time:.4f} seconds")