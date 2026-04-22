from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import os
import json

app = Flask(__name__)
CORS(app)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        image_base64 = data.get("image")
        media_type = data.get("media_type", "image/png")

        prompt = """이 이미지는 한국 채권시장의 수요예측표입니다. 아래 JSON 구조만 반환하세요 (마크다운 없이):
{
  "issuer": "발행회사명",
  "series": "회차",
  "grade": "신용등급",
  "maturity": "만기",
  "issue_amount": 발행금액_억원_숫자,
  "forecast_date": "수요예측일",
  "total_demand": 총참여금액_억원_숫자,
  "participants": [
    { "name": "회사명", "amount": 참여금액_억원_숫자, "bp": bp_숫자 }
  ]
}
규칙:
- 각 행 = 참여기관 1건
- 참여금액: 해당 행 총참여금액 열 숫자(억원)
- bp: 해당 행에 값이 있는 열의 헤더 bp값 (음수 가능, 예: -20, 0, 30)
- 같은 회사가 다른 금리로 참여한 경우 각각 별도 항목
- 숫자는 number 타입
- JSON만 반환"""

        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": prompt}
                ],
            }]
        )

        raw = message.content[0].text
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
        return jsonify({"success": True, "data": parsed})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
