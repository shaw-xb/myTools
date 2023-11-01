
# 忽略pandas 警告
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib.pyplot as mp
from multiprocessing import Pool
import time
import sys



class Grid():
    # 定义1经纬度换算为多少米
    BASE_X = 100000
    BASE_Y = 100000
    # 75.223971, 52.96852
    # 134.28833, 16.83265323
    # 超出以下经纬度则算异常点（非中国范围内的点）
    CHINA_X = [70, 140]
    CHINA_Y = [10, 60]

    def __init__(self, file_path, config_path, point_name, X, Y):
        self.file_path = file_path
        self.config_path = config_path
        self.point_name = point_name
        self.X = X
        self.Y = Y
        self.read_data()
        self.read_config()

    def read_data(self):
        try:
            data = pd.read_excel(self.file_path, dtype={self.X: float, self.Y: float})
            data = data.loc[:, [self.point_name, self.X, self.Y]]
            # 去除有空值的行
            data.dropna(axis=0, how='any', inplace=True)
            # 去除异常经纬度（非中国内的点）
            idx = (self.CHINA_X[0] < data[self.X]) & (data[self.X] < self.CHINA_X[1]) & (
                        self.CHINA_Y[0] < data[self.Y]) & (data[self.Y] < self.CHINA_Y[1])
            data = data[idx]
            data.reset_index(drop=True, inplace=True)
            data['等级'] = None
            self.lt = (data.loc[data[self.X].idxmin(), self.X], data.loc[data[self.Y].idxmax(), self.Y])
            self.rb = (data.loc[data[self.X].idxmax(), self.X], data.loc[data[self.Y].idxmin(), self.Y])
            self.data = data
            print(self.data)
        except BaseException as e:
            print(e)
            sys.exit('源文件经纬度格式异常！（含中文字符串）')

    def read_config(self):
        with open(self.config_path) as f:
            self.level_list = eval(f.read())

    # 创建网格
    def create_grid(self, level):
        self.level = level
        # 创建网格点阵进行测试
        # 默认认为经度10000米是1度，维度10000米是1度
        grid = np.meshgrid(np.arange(self.lt[0], self.rb[0], self.level[1] / self.BASE_X),
                           np.arange(self.lt[1], self.rb[1], -self.level[1] / self.BASE_Y))
        self.grid = np.c_[grid[0].ravel(), grid[1].ravel()]
        print('网格数量：', self.grid.shape[0], '，正在筛选', self.level, '等级...')

    # 将所有点绘制在散点图上
    def show_point(self):
        index = (self.data[self.X] >= self.grid[0, 0]) & (self.data[self.X] <= self.grid[-1, 0]) & (
                self.data[self.Y] <= self.grid[0, 1]) & (self.data[self.Y] >= self.grid[-1, 1])
        # print(index)
        data = self.data[index]

        mp.figure(f'grid{self.level[1]}')
        mp.xticks(self.grid[:, 0])
        mp.yticks(self.grid[:, 1])
        mp.grid()
        mp.scatter(self.grid[:, 0], self.grid[:, 1])
        mp.scatter(data[self.X], data[self.Y], alpha=0.3, c='red')

    # 显示散点图
    def show(self):
        mp.show()

    # 筛选
    def sizer(self):
        # 给每一个点标记其所在的网格
        for i in range(len(self.data)):
            data = self.data.loc[i, :]
            point = np.array(data[[self.X, self.Y]])
            idx = [np.abs(point[0] - self.lt[0]) // (self.level[1] / self.BASE_X),
                   np.abs(point[1] - self.lt[1]) // (self.level[1] / self.BASE_Y)]
            self.data.loc[i, f'{self.level[0]}等级_所在网格'] = f'{int(idx[0])}:{int(idx[1])}'

        # 把所有点根据 所在网格字段 进行分组
        grouped = self.data.groupby(f'{self.level[0]}等级_所在网格')[f'{self.level[0]}等级_所在网格'].count()
        # print(grouped)
        # 依次遍历有点落在其中的网格
        # 使用进程池提高筛选计算效率
        p = Pool()
        for wg in grouped.index:
            p.apply_async(self.sizer_one, args=(wg, grouped), callback=self.mycallback)
        p.close()
        p.join()

    def sizer_one(self, wg, grouped):
        # 落在wg 网内的点
        temp = self.data[self.data[f'{self.level[0]}等级_所在网格'] == wg]
        if temp['等级'].isnull().all():
            # wg网格的中心点经纬度
            center = [self.lt[0] + self.level[1] / self.BASE_X * (int(wg.split(':')[0]) + 0.5),
                      self.lt[1] - self.level[1] / self.BASE_Y * (int(wg.split(':')[1]) + 0.5)]
            # print(center)
            # mp.scatter(center[0],center[1])
            # print(wg, grouped[wg])

            # 计算每个点到中心点的距离
            temp.loc[:, '中心距离'] = ((np.array(temp)[:, 1] - center[0]) ** 2) + (
                    (np.array(temp)[:, 2] - center[1]) ** 2)
            # 获取距离中心点距离最小的点的索引
            min_idx = temp['中心距离'].astype(float).idxmin()
            # 给最靠近中心的点设置当前图层等级
            # 没有等级标记则需在回调函数中设置标记
            return min_idx, 1
        else:
            # 已有等级标签， 则直接取一个做为该区域显示的点，回调函数中不需要重新设置标记
            min_idx = temp[temp['等级'].notnull()].head(1).index
            return min_idx, 0

    # 多进程的回调函数
    def mycallback(self, res):
        if res[-1]:
            self.data.loc[res[0], '等级'] = self.level[0]
        # ----将最靠近中心的点, 或该单元格中已经有标签的点绘制到散点图上(若不需绘图则注释掉)
        # mp.scatter(self.data.loc[res[0], self.X], self.data.loc[res[0], self.Y], c='black')

    def set_level(self):
        for level in self.level_list:
            self.create_grid(level)
            # ----若不需绘图则注释掉
            # self.show_point()
            self.sizer()
            # ----若不需绘图则注释掉
            # self.show()
            print('--'*10)
            print(f'{level}等级，筛选完成！')

    def save_file(self, file_path):
        self.data.to_excel(file_path)


if __name__ == '__main__':
    # 定义源文件路径，读哪些字段， 和等级列表(米)
    file_path = './全国坐标数据.xlsx'
    config_path = './config.txt'
    # 在原文件中需要读取的字段名： 点名，经度、维度
    point_name, X, Y = ['区县', 'X', 'Y']
    # 定义保存路径
    save_path = './res.xlsx'

    # API 按如下步骤调用即可
    beg = time.time()

    # --------------------
    my_test = Grid(file_path, config_path, point_name, X, Y)
    my_test.set_level()
    my_test.save_file(save_path)
    # --------------------

    end = time.time()
    print('共计用时', end - beg, '秒。')
