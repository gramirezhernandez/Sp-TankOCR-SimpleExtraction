
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
key = os.getenv("COMPUTER_VISION_KEY_SP")
endpoint = "https://computer-vision-sp-propane-inspection-dev-us-east.cognitiveservices.azure.com/"

image_path = r"./Images/qsteel1.jpg"   

# ----------------------------
# 3) Keywords list with id + word
# ----------------------------
KEYWORDS = [
    {"manufacturer": "manchester tanks", "word": "manchester"},
    {"manufacturer": "trinity", "word": "trinity"},
    {"manufacturer": "quality steel", "word": "quality"},
    {"manufacturer": "quality steel", "word": "steel"},
    {"manufacturer": "american welding", "word": "american"},
    {"manufacturer": "american welding", "word": "welding"},
    {"manufacturer": "chemitrol", "word": "chemitrol"},
]

# Compile regex patterns for each keyword (whole word, case-insensitive)
keyword_patterns = [
    {"manufacturer": k["manufacturer"], "pattern": re.compile(rf"\b{re.escape(k['word'])}\b", re.IGNORECASE)}
    for k in KEYWORDS
]

# ----------------------------
# 4) Init client and run OCR
# ----------------------------
client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))

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
    raise RuntimeError(f"OCR failed: {result.status}")

# ----------------------------
# 5) Search for keywords and stop when found
# ----------------------------
found_manufacturer = None

for page in result.analyze_result.read_results:
    for line_num, line in enumerate(page.lines, start=1):
        text = line.text
        for kp in keyword_patterns:
            if kp["pattern"].search(text):
                found_manufacturer = kp["manufacturer"]
                break
        if found_manufacturer is not None:
            break
    if found_manufacturer is not None:
        break

# ----------------------------
# 6) Return result (for use in automation or script)
# ----------------------------
if found_manufacturer is not None:
    # Print only the ID (for integration with other systems)
    print(found_manufacturer)
else:
    print("No keywords found.")

end_time = time.time()
exec_time = end_time - ini_time
print("--------")
print(f"Execution time: {exec_time:.4f} seconds")