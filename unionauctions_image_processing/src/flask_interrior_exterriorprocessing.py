# --- Imports ---
from flask import Flask, request, jsonify
import base64, json, cv2, numpy as np, re
from datetime import datetime
from openai import OpenAI
import key  # key.py should contain: apikey = "sk-..."
from PIL import Image

# --- App Setup ---
app = Flask(__name__)
client = OpenAI(api_key=key.apikey)

# --- Utility Functions ---
def image_to_base64(img):
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode("utf-8")

def clean_gpt_response(raw_text):
    # Remove markdown fences and trailing notes
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text.strip())
    cleaned = re.sub(r"```$", "", cleaned).strip()
    # Extract only the JSON block
    match = re.search(r'\{[\s\S]*\}\s*$', cleaned)
    return match.group(0) if match else cleaned

def safe_parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

def annotate_image(image, result):
    h, w, _ = image.shape
    for dmg in result.get("damages", []):
        bbox = dmg["bounding_box"]
        x1, y1, x2, y2 = [int(bbox[0] * w), int(bbox[1] * h), int(bbox[2] * w), int(bbox[3] * h)]
        color = (0, 255, 0) if dmg["damage_type"] == "scratches" else (0, 0, 255)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, dmg["damage_type"], (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return image

def annotate_interior(image, result):
    h, w, _ = image.shape
    for issue in result.get("inspection_report", []):
        bbox = issue.get("bounding_box")
        if isinstance(bbox, dict):
            x1, y1 = int(bbox["x"]), int(bbox["y"])
            x2, y2 = x1 + int(bbox["width"]), y1 + int(bbox["height"])
        elif isinstance(bbox, list) and len(bbox) == 4:
            x1, y1, x2, y2 = [int(bbox[i] * (w if i % 2 == 0 else h)) for i in range(4)]
        else:
            continue
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(image, "", (x1, max(0, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    return image

# --- Prompts ---
exterior_prompt = """
Act as a senior mechanic:

This is a car image. Identify and analyze all visible external damages or defects.

Return each visible damage instance as a separate object. Do not group multiple damages into one. Even if damages are adjacent, overlapping, or in the same region, treat each as distinct. Include faint, partial, or borderline defects. Use a lower confidence threshold if needed to capture subtle damage.

Return a JSON object with:
- "damages": an array of objects, each with:
    - damage_type: one of ['scratches', 'dents']
    - location: e.g. 'front-left fender', 'rear bumper', 'front door'
    - severity: 'minor', 'moderate', 'severe'
    - confidence: float between 0 and 1
    - description: short description of the damage
    - count: number of instances of this damage
    - bounding_box: [x1, y1, x2, y2] in normalized coordinates (0-1 relative to image width/height)
- "summary": object with total counts per damage type
- "text_summary": 2-3 sentence description of overall condition

Rules:
- Return all visible damage instances, even faint or borderline ones.
- Do not merge multiple damages into one object.
- Do not skip faint or partial damages due to low contrast or small size.
- Ignore reflections, shadows, dirt, water spots, or camera artifacts.
- Always provide bounding_box for each detection, based on the actual visible area of damage.
- Do not report 'none' unless absolutely no damage is visible."""

interior_prompt = """
You are an expert automotive inspector. Analyze the given car interior image and identify only the visible problem areas.

Target components:
- Seats - stains, tears, discoloration, missing covers
- Roof lining - sagging, dirt patches, water damage
- Dashboard & console - cracks, dust accumulation, missing knobs
- Door panels - scratches, broken handles, torn fabric
- Floor mats & carpet - dirt, wear, foreign objects
- Rear shelf / boot cover - damage, missing parts
- Other visible areas - misplaced items, trash, unusual wear

For each issue found, return:
- Component name
- Issue type
- Severity (Medium / High)
- Suggested action (Clean / Repair / Replace)
- Confidence score (0-1)
- Bounding box: dictionary with x, y, width, height in pixel units

Also provide a 2-3 sentence description of overall condition.

Exclude clean or non-visible components. Output must be structured in a single JSON object with:
- "inspection_report": array of issue objects
- "text_summary": short description of overall condition

Do not return markdown, bullet points, or any text outside the JSON object.
Do not write any text on the image, just highlight the issue area. Do not show issues with Severity Low."""

# --- Routes ---
@app.route('/exterioranalysis', methods=['POST'])
def analyze_exterior():
    start_time = datetime.now()
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_bytes = request.files['image'].read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": exterior_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]}],
        temperature=0
    )

    raw_text = response.choices[0].message.content
    json_text = clean_gpt_response(raw_text)
    result = safe_parse_json(json_text)

    if not result:
        return jsonify({"error": "Could not parse GPT response", "raw_output": raw_text}), 500

    annotated = annotate_image(image.copy(), result)
    encoded_img = image_to_base64(annotated)
    summary = result.get("summary", {})
    dents = int(summary.get("dents", 0)) if isinstance(summary.get("dents", 0), (int, float)) else 0
    scratches = int(summary.get("scratches", 0)) if isinstance(summary.get("scratches", 0), (int, float)) else 0

    return jsonify({
        "image": encoded_img,
        "summary": f"dents={dents}~scratches={scratches}",
        "text_summary": result.get("text_summary", "")
    })

@app.route('/interioranalysis', methods=['POST'])
def analyze_interior():
    start_time = datetime.now()
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_bytes = request.files['image'].read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": interior_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]}],
        temperature=0
    )

    raw_text = response.choices[0].message.content
    json_text = clean_gpt_response(raw_text)
    result = safe_parse_json(json_text)

    if not result:
        return jsonify({"error": "Could not parse GPT response", "raw_output": raw_text}), 500

    annotated = annotate_interior(image.copy(), result)
    encoded_img = image_to_base64(annotated)
    issues = result.get("inspection_report", [])
    formatted_string = "~".join(f"{issue['component_name']}={issue['issue_type']}" for issue in issues)

    return jsonify({
        "image": encoded_img,
        "summary": formatted_string,
        "text_summary": result.get("text_summary", "")
    })

chasis_engine_prompt = """
System:
You are an Automotive Forensics Vision Analyst. Work only with visual evidence in the provided image(s). Be precise, conservative, and return ONLY valid JSON.
User Task:
Determine whether a photographed engine number is genuine or altered.
Instructions:
- Locate and highlight the engine-number region(s) in the image.
- OCR the engraved identifier (e.g., engine or chassis number) and assess engraving consistency.
- Use the term "engraved identifier" in all summaries to maintain generality across engine and chassis numbers.
- Avoid speculative language unless strong visual evidence demands it. Do not use phrases like "may indicate," "suggests," or "possibly" unless tampering cues are clearly visible.
- If engraving appears clean, consistent, and untampered, return a confident summary using phrases like: "appears cleanly stamped," "no visual evidence of tampering," "corrosion and texture are uniform," and "judgment is based on internal consistency."
- Include analysis explaining the assigned confidence level, based on image clarity, engraving visibility, and consistency of forensic cues.
- Compare against manufacturer-like characteristics:
- Font type & uniformity (stroke width, serif/sans, character shapes)
- Always include the OCR result (engraved identifier) explicitly in the reasoning_summary. Use the format: "The engraved identifier 'XYZ123' appears..." even if tampering is suspected.
- Character size & spacing consistency; baseline alignment/curvature
- Engraving depth & edge profile (clean vs. feathered/burred)
- Surface/finish continuity (paint halo, polishing, grinding, filing marks)
- Texture & corrosion pattern continuity inside vs. outside characters
- Color/reflectance differences suggestive of recent rework or fill
- Check for tampering cues:
- Re-stamping, double impressions, misaligned characters
- Inconsistent fonts/sizes, out-of-sequence VIN subset
- Heat/weld marks, filler/putty, repaint overshoot, sanding swirls
- Selective corrosion/cleaning around digits ("windowing" effect)
- Evaluate image quality gates: blur, glare, shadows, compression, framing
- If reference format is provided, compare deviations. Otherwise, base judgment on internal consistency.

Output Format (strict JSON only):
{
  "overall_verdict": "likely_genuine" | "suspicious" | "altered" | "inconclusive",
  "confidence": 0.0–1.0,
  "reasoning_summary": "2–4 sentences, evidence-based, no speculation. Must include justification for the confidence level. Use 'engraved identifier' instead of 'engine number'."
  "highlighted_region": {
    "bbox_norm": [x, y, w, h]
  }
}

Constraints:
- Output MUST be valid JSON. No markdown, no comments.
- Do not invent manufacturer rules; only use supplied references or visual consistency.
- If uncertain, prefer "inconclusive" or "suspicious" with precise reasons.
"""

@app.route('/chasisengineanalysis', methods=['POST'])
def analyze_chasis_engine():
    start_time = datetime.now()
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_bytes = request.files['image'].read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": chasis_engine_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]}],
        temperature=0
    )

    raw_text = response.choices[0].message.content
    json_text = clean_gpt_response(raw_text)
    result = safe_parse_json(json_text)

    if not result:
        return jsonify({"error": "Could not parse GPT response", "raw_output": raw_text}), 500

    # Optional: draw bounding box if bbox_norm is present
    if "highlighted_region" in result and "bbox_norm" in result["highlighted_region"]:
        h, w, _ = image.shape
        x, y, bw, bh = result["highlighted_region"]["bbox_norm"]
        x1, y1 = int(x * w), int(y * h)
        x2, y2 = int((x + bw) * w), int((y + bh) * h)
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 255, 0), 2)

    encoded_img = image_to_base64(image.copy())
    print(f"result:{ result}")
    return jsonify({
        "image": encoded_img,
        "summary": f"verdict={result.get('overall_verdict')}~confidence={result.get('confidence')}",
        "text_summary": result.get("reasoning_summary", "")
    })

accident_check_prompt = """
System:
You are an expert automotive inspector specializing in under-bonnet (engine bay) forensic analysis for repossessed/auction vehicles. You must carefully analyze provided photos and report evidence of replaced or repaired parts, prior accident repairs, and non-OEM modifications. When uncertain, state so with reasons. Do NOT guess.

User Task:
Assess accident repair evidence based on visible engine bay components.

Instructions:
- Identify visible regions: radiator support, headlamp brackets, strut towers, apron rails, firewall, battery tray, ECU mounts, airbox, wiring harnesses, bonnet latch, etc.
- Check for repair cues: mismatched fasteners, tool marks, paint overspray, non-OEM welds, disturbed sealants, bracket misalignment, corrosion mismatch, fluid stains, etc.
- Infer accident severity if multiple cues cluster in the front clip.
- Use bounding box for any flagged region.
- Justify confidence based on image clarity, cue visibility, and internal consistency.
- Use “engraved identifier” in summary for consistency.

Output Format (strict JSON only):
{
  "overall_verdict": "likely_genuine" | "suspicious" | "altered" | "inconclusive",
  "confidence": 0.0–1.0,
  "reasoning_summary": "2–4 sentences, evidence-based, no speculation. Must include justification for the confidence level. Use 'engraved identifier' instead of 'engine number'.",
  "highlighted_region": {
    "bbox_norm": [x, y, w, h]
  }
}
"""

@app.route('/accidentcheck', methods=['POST'])
def analyze_accident_check():
    start_time = datetime.now()
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_bytes = request.files['image'].read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": accident_check_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]}],
        temperature=0
    )

    raw_text = response.choices[0].message.content
    json_text = clean_gpt_response(raw_text)
    result = safe_parse_json(json_text)

    if not result:
        return jsonify({"error": "Could not parse GPT response", "raw_output": raw_text}), 500

    # Optional: draw bounding box if bbox_norm is present
    if "highlighted_region" in result and "bbox_norm" in result["highlighted_region"]:
        h, w, _ = image.shape
        x, y, bw, bh = result["highlighted_region"]["bbox_norm"]
        x1, y1 = int(x * w), int(y * h)
        x2, y2 = int((x + bw) * w), int((y + bh) * h)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
    else:
        result["highlighted_region"] = {"bbox_norm": [0.0, 0.0, 0.0, 0.0]}

    encoded_img = image_to_base64(image.copy())
    print(f"result:{ result}")
    return jsonify({
        "image": encoded_img,
        #"summary": None,
        "summary": f"verdict={result.get('overall_verdict')}~confidence={result.get('confidence')}",
        "text_summary": result.get("reasoning_summary", "")
    })

accident_check_prompt = """
System:
You are an expert automotive inspector specializing in under-bonnet (engine bay) forensic analysis for repossessed/auction vehicles. You must carefully analyze provided photos and report evidence of replaced or repaired parts, prior accident repairs, and non-OEM modifications. When uncertain, state so with reasons. Do NOT guess.

User Task:
Assess accident repair evidence based on visible engine bay components.

Instructions:
- Identify visible regions: radiator support, headlamp brackets, strut towers, apron rails, firewall, battery tray, ECU mounts, airbox, wiring harnesses, bonnet latch, etc.
- Check for repair cues: mismatched fasteners, tool marks, paint overspray, non-OEM welds, disturbed sealants, bracket misalignment, corrosion mismatch, fluid stains, etc.
- Infer accident severity if multiple cues cluster in the front clip.
- Justify confidence based on image clarity, cue visibility, and internal consistency.
- Use “engraved identifier” in summary for consistency.

Output Format (strict JSON only):
{
  "overall_verdict": "likely_genuine" | "suspicious" | "altered" | "inconclusive",
  "confidence": 0.0–1.0,
  "reasoning_summary": "2–4 sentences, evidence-based, no speculation. Must include justification for the confidence level. Use 'engraved identifier' instead of 'engine number'."
}
"""

@app.route('/accidentcheckmulti', methods=['POST'])
def analyze_accident_check2():
    start_time = datetime.now()

    if 'images' not in request.files:
        return jsonify({"error": "No images uploaded"}), 400

    images = request.files.getlist('images')
    if not images:
        return jsonify({"error": "Empty image list"}), 400

    messages = [{
        "role": "user",
        "content": [{"type": "text", "text": accident_check_prompt}]
    }]

    for img_file in images:
        image_bytes = img_file.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0
        )
    except Exception as e:
        return jsonify({"error": f"GPT request failed: {str(e)}"}), 500

    raw_text = response.choices[0].message.content
    json_text = clean_gpt_response(raw_text)
    result = safe_parse_json(json_text)

    if not result:
        return jsonify({"error": "Could not parse GPT response", "raw_output": raw_text}), 500

    return jsonify({
        "image": None,
        "summary": f"verdict={result.get('overall_verdict')}~confidence={result.get('confidence')}",
        "text_summary": result.get("reasoning_summary", "")
    })


# --- Run ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)