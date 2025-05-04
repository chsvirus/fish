from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store the latest sensor data from ESP32
latest_sensor_data = {
    "temperature": 0.0,
    "tds": 0.0,
    "ph": 0.0,
    "do": 0.0,
    "waterLevel": 0.0,
    "waterPump": 0,
    "oxygenPump": 0,
    "filter": 0,
    "fan": 0,
    "mode": "AUTO",
    "status": 0
}

@app.route('/chat')
def chat():
    q = request.args.get('q')
    if not q:
        return jsonify({"response": "Please provide a question."})
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in fish environments.sumrize your respone to 7 words"},
                {"role": "user", "content": q}
            ]
        )
        return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/update_sensors', methods=['POST'])
def update_sensors():
    """ESP32 sends sensor data to this endpoint"""
    global latest_sensor_data
    try:
        data = request.json
        latest_sensor_data.update(data)
        print(f"Received sensor data: {data}")
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/ai_control', methods=['GET'])
def ai_control():
    """ESP32 polls this endpoint to get AI control decisions"""
    try:
        # Generate AI decision based on current sensor data
        ai_decision = get_ai_decision(latest_sensor_data)
        
        print(f"AI Decision: {ai_decision}")
        return jsonify(ai_decision)
    except Exception as e:
        return jsonify({"error": str(e)})

def get_ai_decision(sensor_data):
    """Use AI to make decisions based on sensor data"""
    
    # Create a detailed prompt for the AI
    prompt = f"""You are an AI managing a fish tank system. Based on this data, decide what to do:

Temperature: {sensor_data['temperature']}°C
TDS: {sensor_data['tds']} ppm
pH: {sensor_data['ph']}
Dissolved Oxygen (DO): {sensor_data['do']} mg/L
Water Level: {sensor_data['waterLevel']} cm
Current Status: {'CRITICAL' if sensor_data['status'] == 2 else 'WARNING' if sensor_data['status'] == 1 else 'NORMAL'}

THRESHOLDS:
- Temperature: 20-28°C
- TDS: 100-500 ppm
- pH: 6.5-8.0
- DO: minimum 5.0 mg/L
- Water Level: target 15 cm

Current device states:
- Water Pump: {'ON' if sensor_data['waterPump'] else 'OFF'}
- Oxygen Pump: {'ON' if sensor_data['oxygenPump'] else 'OFF'}
- Filter: {'ON' if sensor_data['filter'] else 'OFF'}
- Fan: {'ON' if sensor_data['fan'] else 'OFF'}

You can control:
1. WATER PUMP: Use for controlling water level
2. OXYGEN PUMP: Use for DO and pH correction
3. FILTER: Use for high TDS
4. FAN: Use for high temperature

Provide control decisions as a JSON object with:
- waterPump: 1 for ON, 0 for OFF
- oxygenPump: 1 for ON, 0 for OFF
- filter: 1 for ON, 0 for OFF
- fan: 1 for ON, 0 for OFF

ONLY provide the JSON object, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that controls a fish tank. Respond ONLY with JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Lower temperature for more consistent responses
        )
        
        # Parse the JSON response
        import json
        decision = json.loads(response.choices[0].message.content)
        
        # Ensure we have all necessary keys
        control_keys = ['waterPump', 'oxygenPump', 'filter', 'fan']
        for key in control_keys:
            if key not in decision:
                decision[key] = sensor_data[key]  # Keep current state if not specified
        
        return decision
        
    except Exception as e:
        print(f"Error in AI decision: {e}")
        # Return current state if AI fails
        return {
            'waterPump': sensor_data['waterPump'],
            'oxygenPump': sensor_data['oxygenPump'],
            'filter': sensor_data['filter'],
            'fan': sensor_data['fan']
        }

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
