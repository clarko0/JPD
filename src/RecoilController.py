import random
import sys
import time
from src.Constants import Constants
import json
from dto.Gun import Gun
from dto.GameConfig import GameConfig
import multiprocessing
from multiprocessing import Process, Queue, Pipe
import win32api
from src.Overlay import Overlay
import win32con
from PyQt5 import QtWidgets


class RecoilController:

    def __init__(self) -> None:

        self.guns = self.__import_gun_data()

        self.game_config = self.__get_config()

        self.mouse_queue = Queue(1)

        self.CURRENT_WEAPON: Gun = self.guns[0]

    def __import_gun_data(self) -> list[Gun]:

        with open(Constants.GUN_DATA_PATH) as file:
            gun_data = json.load(file)

        res = [Gun(WT=gun_data[data]['WT'],
                   MIN_CT=gun_data[data]['MIN_CT'],
                   MAX_CT=gun_data[data]['MAX_CT'],
                   AMMO_AMOUNT=gun_data[data]['AMMO_AMOUNT'],
                   TAP=gun_data[data]['TAP'],
                   VIEW_ANGLES=gun_data[data]['VIEW_ANGLES'],
                   NAME=data) for data in gun_data]

        return res

    def __get_config(self) -> GameConfig:

        game_config = GameConfig()

        try:
            with open(Constants.GAME_CONFIG_PATH) as file:
                config_lines = file.readlines()

            for line in config_lines:

                value = float(line.split('"')[1])

                if 'input.sensitivity' in line:
                    game_config.SENSITIVITY = value

                if "graphics.fov" in line:
                    game_config.FOV = value

                if "input.ads_sensitivity" in line:
                    game_config.ADS_FACTOR = value

                if "graphics.ui_scale" in line:
                    game_config.UI_SCALE = value
        except:
            game_config.SENSITIVITY = 0.5
            game_config.FOV = 90
            game_config.ADS_FACTOR = 1
            game_config.UI_SCALE = 1

        game_config.SCREENMULTIPLYER = (-0.03 *
                                        game_config.SENSITIVITY * 3 * (game_config.FOV / 100))
        game_config.SCREENMULTIPLYER_CROUCH = (
            -0.03 * (game_config.SENSITIVITY * 2) * 3 * (game_config.FOV / 100))

        return game_config

    def move_mouse(self) -> None:

        while True:
            try:
                move_data = self.mouse_queue.get()
                out_x, out_y, click = move_data[0], move_data[1], move_data[2]
            except:
                continue

            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE,
                                 int(out_x), int(out_y), 0, 0)

    def __calculate_pixels(self, CW_VA_X: float, CW_VA_Y: float, holo: bool) -> tuple[float, float]:
        scope = 1

        if holo:
            scope = 1.2

        MovePenalty = 1

        if (win32api.GetAsyncKeyState(0x41) < 0 or win32api.GetAsyncKeyState(0x44) < 0 or win32api.GetAsyncKeyState(0x57) < 0 or win32api.GetAsyncKeyState(0x53) < 0):

            MovePenalty = 1.18

        if (win32api.GetAsyncKeyState(0x11) < 0 or win32api.GetAsyncKeyState(0x43) < 0):

            CW_PX_X = ((CW_VA_X * scope) *
                       MovePenalty) / self.game_config.SCREENMULTIPLYER_CROUCH

            CW_PX_Y = ((CW_VA_Y * scope) *
                       MovePenalty) / self.game_config.SCREENMULTIPLYER_CROUCH

            return CW_PX_X, CW_PX_Y

        CW_PX_X = ((CW_VA_X * scope)
                   * MovePenalty) / self.game_config.SCREENMULTIPLYER

        CW_PX_Y = ((CW_VA_Y * scope)
                   * MovePenalty) / self.game_config.SCREENMULTIPLYER

        return CW_PX_X, CW_PX_Y

    def sleep_time(self, wt):
        target_time = time.perf_counter() + (wt / 1000)
        while time.perf_counter() < target_time:
            pass

    def __linear_interpolation(self, wt, ct, x1: float, y1: float, start_time: float):

        x_, y_, t_ = 0, 0, 0

        for i in range(1, int(ct) + 1):
            xI = i * x1 // ct
            yI = i * y1 // ct
            tI = (i * ct) // ct

            self.mouse_queue.put([xI - x_, yI - y_, 0])
            self.sleep_time(tI - t_)
            x_, y_, t_ = xI, yI, tI

        loop_time = (time.perf_counter() - start_time) * 1000
        self.sleep_time(wt - loop_time)

    def redraw_overlay(self):
        try:
            self.overlay.terminate()
        except:
            pass

        self.overlay = Process(target=self.draw_overlay)
        self.overlay.daemon = True
        self.overlay.start()

    def __handle_recoil(self) -> None:

        CW_VA_X, CW_VA_Y = 0, 0

        prev_time_error = 0
        repeat_delay_start = 0
        diff = 0
        xyxy_all = []
        holo = False
        diff_stats = []
        bullet_num = []

        bullet_count = 0
        CT_AVG = 0
        diff_dict = {i: [] for i in range(1, 31)}

        while True:

            start = time.perf_counter()

            if (((start - repeat_delay_start) * 1000) > (self.CURRENT_WEAPON.WT) or bullet_count >= self.CURRENT_WEAPON.AMMO_AMOUNT):

                CT_AVG = 0
                bullet_count = 0
                prev_time_error = 0

            while (win32api.GetAsyncKeyState(0x01) < 0 and win32api.GetAsyncKeyState(0x02) < 0):

                compass_time = time.perf_counter()

                current_time = ((time.perf_counter() - compass_time) * 1000)

                if (self.CURRENT_WEAPON.TAP):

                    CW_VA_X, CW_VA_Y = self.CURRENT_WEAPON.VIEW_ANGLES[
                        0], self.CURRENT_WEAPON.VIEW_ANGLES[1]

                else:

                    CW_VA_X, CW_VA_Y = self.CURRENT_WEAPON.VIEW_ANGLES[bullet_count][
                        0], self.CURRENT_WEAPON.VIEW_ANGLES[bullet_count][1]

                CW_PX_X, CW_PX_Y = self.__calculate_pixels(
                    CW_VA_X, CW_VA_Y, holo)

                CW_CT = random.randint(
                    self.CURRENT_WEAPON.MIN_CT, self.CURRENT_WEAPON.MAX_CT)

                current_time = (time.perf_counter() - start) * 1000

                self.__linear_interpolation(
                    self.CURRENT_WEAPON.WT, self.CURRENT_WEAPON.MAX_CT - current_time, CW_PX_X, CW_PX_Y, start)

                ct = time.perf_counter()

                print("Time:", (ct - start) * 1000,
                      "Goal:", self.CURRENT_WEAPON.WT)

                prev_time_error += (ct - start) * 1000 - self.CURRENT_WEAPON.WT
                print(prev_time_error)

                start = ct

                repeat_delay_start = ct

                while (self.CURRENT_WEAPON.TAP and win32api.GetAsyncKeyState(0x01) < 0):
                    pass

                if (bullet_count < self.CURRENT_WEAPON.AMMO_AMOUNT - 1):
                    bullet_count += 1

            if win32api.GetAsyncKeyState(0x30) < 0:

                print("Changing weapon")

                next_index = self.guns.index(self.CURRENT_WEAPON) + 1

                if next_index >= len(self.guns):
                    next_index = 0

                self.CURRENT_WEAPON = self.guns[next_index]

                self.redraw_overlay()

                self.sleep_time(200)

                print("New weapon: ", self.CURRENT_WEAPON.NAME)

            if win32api.GetAsyncKeyState(0x39) < 0:

                next_index = self.guns.index(self.CURRENT_WEAPON) - 1

                if next_index < 0:
                    next_index = len(self.guns) - 1

                self.CURRENT_WEAPON = self.guns[next_index]

                self.redraw_overlay()

                self.sleep_time(200)

                print("New weapon: ", self.CURRENT_WEAPON.NAME)

            if win32api.GetAsyncKeyState(0x28) < 0:
                while win32api.GetAsyncKeyState(0x28) < 0:
                    holo = not holo

                print("Scope: ", holo)

    def draw_overlay(self):
        global overlay
        app1 = QtWidgets.QApplication(sys.argv)

        overlay = Overlay(windowSize=24, penWidth=1,
                          weapon=self.CURRENT_WEAPON.NAME, scope="Nil")
        overlay.show()

        app1.exec_()

    def change_weapon(self) -> None:

        while True:

            while win32api.GetAsyncKeyState(0x30) < 0:

                print("Changing weapon")

                next_index = self.guns.index(self.CURRENT_WEAPON) + 1

                if next_index >= len(self.guns):
                    next_index = 0

                self.CURRENT_WEAPON = self.guns[next_index]

                print("New weapon: ", self.CURRENT_WEAPON.NAME)

                self.sleep_time(200)

    def run(self) -> None:
        multiprocessing.freeze_support()

        mouse = Process(target=self.move_mouse)
        mouse.daemon = True
        mouse.start()

        self.redraw_overlay()

        # weapon = Process(target=self.change_weapon)
        # weapon.daemon = True
        # weapon.start()

        self.__handle_recoil()
