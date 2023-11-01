import copy
# encoding=utf-8
import logging
import json
import os

import numpy
import pandas as pd

# %(levelno)s: 打印日志级别的数值
# %(levelname)s: 打印日志级别名称
# %(pathname)s: 打印当前执行程序的路径，其实就是sys.argv[0]
# %(filename)s: 打印当前执行文件名
# %(funcName)s: 打印日志的当前函数
# %(lineno)d: 打印日志的当前行号
# %(asctime)s: 打印日志的时间
# %(thread)d: 打印线程ID
# %(threadName)s: 打印线程名称
# %(process)d: 打印进程ID
# %(message)s: 打印日志信息


format_string = "%(asctime)s|%(levelname)-8s:【%(filename)s|%(funcName)s|%(lineno)d】| %(message)s"
date_format = "%Y-%m-%d %H:%M:%S %p"

logging.basicConfig(filename='./DataProcesser.log',format=format_string,datefmt=date_format,level=logging.DEBUG, encoding="utf-8")

logger = logging.getLogger()


class DataProcess:
    def __init__(self, inputPath, outputPath, templateFile, substationFile):
        self.inputPath = inputPath
        self.outputPath = outputPath
        self.templateFile = templateFile

        self.lineType = ""
        self.hasPointType = False
        self.substation = self.initSubstation(substationFile)

    def process(self):
        try:
            for root, dirs, files in os.walk(self.inputPath):
                logger.info("===============")
                logger.info(root)  # 当前目录路径（包含所有子目录）
                logger.info("===============")
                for file in files:
                    logger.info(f"即将处理：{file}")
                    logger.info(f"文件：{file} | 开始处理...")
                    # self.readCSVToJson(file, root)
                    self.readXlsxToJson(file, root)
                    logger.info(f"文件：{file} | 处理结束!")
        except Exception as e:
            logger.error(f"程序发生异常，详细信息如下：")
            logger.error(e, exc_info=True, stack_info=True)


    def readCSVToJson(self, fileName:str, basePath:str):
        allPoint = dict()
        allLine = dict()
        with open(os.path.join(basePath, fileName), encoding="utf-8") as f:
            data = f.readlines()

        if len(data) >= 2:
            # 获取线路类型
            firstRow = data[0].split(",")
            if firstRow[1] != "设备类型":
                self.lineType = data[1].split(",")[3]
                self.hasPointType = False
            elif firstRow[1] == "设备类型":
                self.lineType = data[1].split(",")[4]
                self.hasPointType = True
            else:
                logger.error(f"文件：{fileName} | 该文件格式未适配，请检查！")

        else:
            logger.error(f"文件：{fileName} | 数据不完整！请检查数据源!")
            return
        for d in data[1:]:
            row = d.split(",")
            self.handleRow(row, allPoint, allLine, fileName)

        logger.info(f"文件：{fileName} | 开始构造geojson...")
        geoJson = self.getShpGeoJson(allPoint, allLine, fileName)
        geoJsonFileName = fileName.split(".csv")[0]
        outputPath = basePath.replace(self.inputPath, self.outputPath)
        # 创建输出路径
        os.makedirs(outputPath, exist_ok=True)
        with open(f"{os.path.join(outputPath, geoJsonFileName)}.json", "w", encoding="utf-8") as f:
            json.dump(geoJson, f)

    def readXlsxToJson(self, fileName:str, basePath:str):
        allPoint = dict()
        allLine = dict()
        if fileName.split('.')[-1] == "xls":
            df = pd.read_excel(os.path.join(basePath, fileName), engine='xlrd')
        elif fileName.split('.')[-1] == "xlsx":
            df = pd.read_excel(os.path.join(basePath, fileName), engine='openpyxl')

        if len(df) >= 1:
            # 获取线路类型
            colName = df.columns
            if df.columns[1] != "设备类型":
                self.lineType = df.iloc[0,:][3]
                self.hasPointType = False
            elif df.columns[1] == "设备类型":
                self.lineType = df.iloc[0,:][4]
                self.hasPointType = True
            else:
                logger.error(f"文件：{fileName} | 该文件格式未适配，请检查！")

        else:
            logger.error(f"文件：{fileName} | 数据不完整！请检查数据源!")
            return
        for row in df.itertuples(index=False):
            self.handleRow(row, allPoint, allLine, fileName)

        logger.info(f"文件：{fileName} | 开始构造geojson...")
        geoJson = self.getShpGeoJson(allPoint, allLine, fileName)
        if fileName.split('.')[-1] == "xls":
            geoJsonFileName = fileName.split(".xls")[0]
        elif fileName.split('.')[-1] == "xlsx":
            geoJsonFileName = fileName.split(".xlsx")[0]
        outputPath = basePath.replace(self.inputPath, self.outputPath)
        # 创建输出路径
        os.makedirs(outputPath, exist_ok=True)
        with open(f"{os.path.join(outputPath, geoJsonFileName)}.json", "w", encoding="utf-8") as f:
            json.dump(geoJson, f)


    def handleRow(self, row, allPoint, allLine, fileName):

        if not self.hasPointType:
            pointName = row[1]
            if pointName is numpy.NAN:
                return
            tName = row[2]
            myPoint = MyPoint("", row[1], tName, row[4], row[5])
        else:
            pointName = row[2]
            if pointName is numpy.NAN:
                return
            tName = row[3]
            myPoint = MyPoint(row[1], row[2], tName, row[5], row[6])

        # 保存点
        allPoint[pointName] = myPoint

        # 添加到线
        lineName = myPoint.lineName
        points = allLine.get(lineName)
        if points:
          points.append(myPoint)
        else:
            allLine[lineName] = [myPoint]


    def getShpGeoJson(self, allPoint, allLine, fileName):
        with open(self.templateFile, 'r', encoding='utf-8') as f:
            tempFile = json.load(f)

        features = tempFile.get("features")
        featureTemplate = features.pop()

        for lineName, points in allLine.items():
            feature = copy.deepcopy(featureTemplate)
            # 具体某一条线
            xy = []
            # 点按名称排序
            points = sorted(points, key=lambda p : p.pointName)
            # 如果此线段起点有T接杆塔，则T接杆塔为第一个点
            if points[0].hasTPoint():
                tName = points[0].tName
                tPoint = allPoint.get(tName)
                if tPoint == None:
                    # 可能是变电站
                    if self.substation.get(tName):
                        xy.append(self.substation.get(tName))
                    else:
                        logger.warning(f"文件：{fileName} | 【{points[0].pointName}】 有T接杆塔，但未找到对应的T接杆塔 【{tName}】！")
                else:
                    xy.append([tPoint.longitude, tPoint.latitude])


            for p in points:
                xy.append([p.longitude, p.latitude])

            # 如果点数量小于2则无法构成线
            if len(xy) < 2:
                logger.warning(f"文件：{fileName} | 线路：{lineName}，杆塔数量小于2！请核对！")
                continue
            feature["attributes"]["type"] = lineName
            feature["geometry"]["paths"][0]= xy

            features.append(feature)

        return tempFile

    def initSubstation(self, substationFile):
        substations = dict()
        with open(substationFile, 'r', encoding='utf-8') as f:
            rows = f.readlines()
        for r in rows[1:]:
            row = r.split(',')
            substations[row[2]] = [float(row[3]), float(row[4])]
        return substations


# 点对象定义
class MyPoint:

    def __init__(self, pointType:str, pointName:str, tName, longitude:float, latitude:float):
        self.pointType = pointType
        self.pointName = pointName
        self.tName = tName
        self.longitude =longitude
        self.latitude = latitude
        self.lineName = self.convertLineName(self.pointName)

    # 是否含有T接杆塔
    def hasTPoint(self):
        return False
        # return not (self.tName is numpy.NAN or self.tName == "")

    def convertLineName(self, pointName):
        res = pointName.rsplit('#', 1)[0]
        return res

    def getPointName(self):
        return self.pointName





if __name__ == '__main__':

    inputPath = './data'
    outputPath = './data_json'
    templateFile = './config/template.json'
    substationFile = './config/变电站.csv'
    dataProcess = DataProcess(inputPath, outputPath, templateFile, substationFile)
    dataProcess.process()
