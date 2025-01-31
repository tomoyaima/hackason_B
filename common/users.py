from datetime import datetime, timezone, timedelta
import os
import cv2
from common.libs import *

class User:
    def __init__(self, id):
        self.id_ = id
        self.JST_ = timezone(timedelta(hours=+9), 'JST')
        self.start_t_ = 0
        self.nowatching_count_ = 1
        self.detector_ = SightDetector()
        self.image_ = []

        self.image_frame_rate = 3
        self.watching = False
        self.caution_flag = False
        self.caution_level = 0
        self.caution_time = 5.0
        self.detector_.frame_rate = self.image_frame_rate
        self.concentration = -1

        # self.slack_apitoken_ = get_slack_apitoken(id)
        # self.slack_channels_ = get_slack_channels(id)
        # self.have_slackbot_ = False
        # if self.slack_apitoken_ and self.slack_channels_:
        #     self.slack_ = SlackBot(id, self.slack_apitoken_, self.slack_channels_)
        #     self.have_slackbot_ = True
        # self.slack_caution_level = 5


    def start_watching(self):
        """Userが画面を見始めたらスタート時刻を記録"""
        if not self.watching:
            self.start_t_ = datetime.now(self.JST_)
            self.watching = True
            print('<--------------------記録スタート-------------------->')

    def end_watching(self):
        """Userが画面見ていない判定になったら開始時刻と終了時刻をDBへ記録"""
        if self.watching:
            self.record_watching_time()
            self.watching = False
            self.caution_level = 0
            print('<--------------------視聴履歴記録完了!-------------------->')

    def record_watching_time(self):
        """視聴履歴をDBに記録"""
        document_update(self.id_, self.start_t_, datetime.now(self.JST_))

    def reset_watching_database(self):
        """DBの視聴履歴をリセット"""
        document_set(self.id_)

    def img_process(self, img):
        """顔の画像処理"""
        self.image_ = img
        result = self.detector_.detect(img)
        if result and not self.watching:
            """視聴開始"""
            self.start_watching()
        elif not result and self.watching:
            """サボり開始"""
            self.end_watching()
        if result:
            self.nowatching_count_ = 1
            self.caution_level = 0
            self.concentration = self.detector_.concentration
        else:
            self.nowatching_count_ += 1
        # self.detector_.print_debug()

    def is_require_caution(self):
        """注意が必要かどうか(返り値 bool)"""
        if self.nowatching_count_ % (self.image_frame_rate * self.caution_time) == 0:
            self.caution_level += 1
            return True
        else :
            return False

    def detector_setup(self, nowatthing_time, watching_time, caution_time):
        """視線検出の設定"""
        self.detector_.nowathing_time = nowatthing_time     # 何秒見ていないとサボり判定か
        self.detector_.watching_time = watching_time        # 何秒見ていると視聴判定か
        self.caution_time = caution_time                    # 何秒サボり判定を連続で食らうと警告レベルを上げるか

    def slack_send_image(self):
        if self.have_slackbot_:
            file_path = os.getcwd() + '/image.jpg'
            cv2.imwrite(file_path, self.image_)
            self.slack_.send_file(file_path)
        else:
            print('This user dont have slack api!!')

    def slack_message(self, message):
        if self.have_slackbot_:
            self.slack_.send_message(message)
        else:
            print('This user dont have slack api!!')

    def slack_sabotage_notice(self):
        self.slack_message('こいつサボりです')
        self.slack_send_image()


class Users:
    def __init__(self):
        self.n = 0
        self.login_users = {}

    def add_login_user(self, id):
        """ログインしているUserの追加"""
        if id not in self.login_users.keys():
            self.login_users[id] = User(id)
            self.n += 1
        else:
            print('This user is already login!')

    def logout_user(self, id):
        """ログアウトしたUserの削除"""
        if id in self.login_users.keys():
            del(self.login_users[id])
            self.n += 1
        else:
            print('logout error!')

    def get_user(self, id):
        """idを指定してUserの取得"""
        if id in self.login_users.keys():
            return self.login_users[id]

