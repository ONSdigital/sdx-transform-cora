from transform import app
import os


if __name__ == '__main__':
    # Startup
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
