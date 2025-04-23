from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)
client = openai.OpenAI(api_key=os.getenv("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"))  # New client style

@app.route('/chat')
def chat():
    q = request.args.get('q')
    if not q:
        return jsonify({"response": "Please provide a question."})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in fish environments."},
                {"role": "user", "content": q}
            ]
        )
        return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
