import sys
import json
import os
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QProgressBar, QListWidget, QLineEdit, QHBoxLayout
)

from downloader import fetch_recovery_list, find_model, download_with_progress, extract
from utils import load_state, save_state
from notifier import notify_discord, notify_slack
from logger import setup_logger


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChromeOS Tool (Advanced)")
        self.logger = setup_logger()

        self.layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        hbox = QHBoxLayout()
        self.input = QLineEdit()
        btn_add = QPushButton("追加")
        btn_add.clicked.connect(self.add_target)
        hbox.addWidget(self.input)
        hbox.addWidget(btn_add)
        self.layout.addLayout(hbox)

        self.progress = QProgressBar()
        self.layout.addWidget(self.progress)

        self.log = QTextEdit()
        self.layout.addWidget(self.log)

        self.btn = QPushButton("実行")
        self.btn.clicked.connect(self.run)
        self.layout.addWidget(self.btn)

        self.setLayout(self.layout)

        self.load_config()

    def log_print(self, msg):
        self.log.append(msg)
        self.logger.info(msg)

    def load_config(self):
        with open("config.json", encoding="utf-8") as f:
            self.config = json.load(f)

        self.list_widget.clear()
        for t in self.config["targets"]:
            self.list_widget.addItem(t)

    def save_config(self):
        targets = [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
        ]
        self.config["targets"] = targets

        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def add_target(self):
        val = self.input.text().strip()
        if val:
            self.list_widget.addItem(val)
            self.input.clear()
            self.save_config()

    def update_progress(self, value):
        self.progress.setValue(value)

    def process_target(self, target, data, state):
        model = find_model(data, target)
        if not model:
            return f"{target}: 見つからない"

        url = model["url"]
        version = model.get("version", "unknown")

        prev = state.get(target)

        if prev == version:
            return f"{target}: 更新なし"

        filename = os.path.join(
            self.config["download_dir"],
            url.split("/")[-1]
        )

        status = download_with_progress(
            url, filename, self.update_progress
        )

        if self.config["auto_extract"]:
            extract(filename, self.config["download_dir"])

        msg = f"{target} updated: {version}"
        notify_discord(self.config["notify"]["discord_webhook"], msg)
        notify_slack(self.config["notify"]["slack_webhook"], msg)

        state[target] = version

        return f"{target}: 更新完了 ({status})"

    def run(self):
        data = fetch_recovery_list()
        state = load_state()

        os.makedirs(self.config["download_dir"], exist_ok=True)

        targets = [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
        ]

        with ThreadPoolExecutor(max_workers=3) as executor:
            results = executor.map(
                lambda t: self.process_target(t, data, state),
                targets
            )

        for r in results:
            self.log_print(r)

        save_state(state)
        self.log_print("完了")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec_())
