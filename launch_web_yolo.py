import threading
import time
import webbrowser

from web_yolo_app import app


def _open_browser() -> None:
    time.sleep(1.0)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
