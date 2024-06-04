from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/update-data', methods=['POST'])
def update_data():
    data = request.json  # Excel'den gelen JSON verisi
    # Verileri işleyin ve uygun bir şekilde saklayın (örneğin, veritabanına kaydedebilirsiniz)
    print("Gelen veri:", data)
    return jsonify({"message": "Veri başarıyla güncellendi"})

if __name__ == '__main__':
    app.run(debug=True)
