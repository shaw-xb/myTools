#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import unicode_literals, division, absolute_import, print_function
# from shaw.myfunc import Jump2directory
# from myfunc import Jump2directory
import sys
import re
from lxml import etree


class Jump2directory():

    def __init__(self, bk):
        self.bk = bk
        self.bit = 3

    # 处理 toc.ncx
    def processNcx(self):
        id = "toc_ncx"
        html = self.bk.readfile(id)
        html_original = html
        xml, ns = self.getXml(html)
        # 获取 navPoint 节点 列表
        navPointList = xml.findall("{0}navMap//{0}navPoint".format(ns))
        if navPointList:
            for navPoint in navPointList:
                playOrder = navPoint.attrib.get("playOrder")
                content = navPoint.find("{0}content".format(ns))
                src = content.attrib.get("src")
                deep = self.playOrder2DeepDic.get(playOrder)
                if deep == "1":
                    src = src.split("#")[0]
                else:
                    src = src.split("#")[0] + "#a{}".format(playOrder.zfill(self.bit))
                content.set("src", src)
        html = etree.tostring(xml, encoding="utf-8").decode("utf-8")
        if not html == html_original:
            self.bk.writefile(id, html)

    # 判断是否有toc.xhtml 没有则不处理
    def isProcess(self):
        flag = False
        textList = [file for file,_ in self.bk.text_iter()]
        # print(textList)
        if "toc.xhtml" in textList:
            flag = True
        else:
            print("未找到 toc.xhtml 目录文件...")
        return flag

    # 解析xml
    def getXml(self, html):
        xml = etree.fromstring(html.encode("utf-8"))
        ns = xml.nsmap.get(None)
        ns = "{%s}" % ns
        return xml, ns


    # 分析toc.ncx文件， 获取目录关键信息
    def getTocInfo(self):
        html = self.bk.readfile(self.bk.gettocid())
        xml, ns = self.getXml(html)
        # 获取 navPoint 节点 列表
        navPointList = xml.findall("{0}navMap//{0}navPoint".format(ns))
        navDic = {}
        playOrder2DeepDic = {}
        for navPoint in navPointList:
            fileName, navInfo = self.getnavPointInfo(navPoint, ns)
            deep = navInfo["deep"]
            playOrder = navInfo["playOrder"]
            playOrder2DeepDic[playOrder] = deep
            self.addnavInfo(navDic, fileName, navInfo)
        # print(navDic, playOrder2DeepDic)
        return navDic, playOrder2DeepDic


    # 提取一个标题的信息
    def getnavPointInfo(self, navPoint, ns):
        navDic = {}
        baseDeep = 1
        navDic["deep"] = str(self.getDeep(navPoint, ns, baseDeep))
        navDic["id"] = navPoint.attrib.get("id")
        navDic["playOrder"] = navPoint.attrib.get("playOrder")
        navDic["title"] = navPoint.findall("{0}navLabel/{0}text".format(ns))[0].text
        src = navPoint.findall("{0}content".format(ns))[0].attrib.get("src")
        fileName = re.findall(r'Text/(.*?.xhtml)', src)[0]
        return fileName, navDic


    def addnavInfo(self,navDic, fileName, navInfo):
        if fileName not in navDic:
            navDic[fileName] = []
        navDic[fileName].append(navInfo)

    # 递归获取标题的深度
    def getDeep(self, navPoint, ns, baseDeep):
        pNode = navPoint.getparent()
        if pNode.tag == "{}navMap".format(ns):
            return baseDeep
        else:
            baseDeep += 1
            return self.getDeep(pNode,ns, baseDeep)

    # 处理toc.xhtml 目录文件
    def processTocXhtml(self,html):
        xml, ns = self.getXml(html)
        # 获取 标题 a 节点 列表
        aList = xml.findall("{0}body//{0}a".format(ns))
        # print(aList)
        for a in aList:
            playOrder =  str(aList.index(a)+1)
            deep = int(self.playOrder2DeepDic.get(playOrder))
            if deep == 1:
                self.setTocXhtml_h1(a, playOrder, deep, ns)
            else:
                self.setTocXhtml_hO(a, playOrder, deep, ns)

        html = etree.tostring(xml, encoding="utf-8").decode("utf-8")
        # print('1')
        return html


    def setTocXhtml_h1(self, a, playOrder, deep, ns):
        span = etree.Element("span")
        text = a.text
        a.text = None
        if not text:
            text = a.find("{}span".format(ns)).text
        href = a.attrib.get("href").split("#")[0]
        # 一级标题的 href 不变，所以不做处理
        a.set("href", href)
        if a.getchildren():
            span = a.getchildren()[0]
            span.set("id", "t{}".format(playOrder.zfill(self.bit)))
        else:
            span.set("id", "t{}".format(playOrder.zfill(self.bit)))
            span.text = text
            a.append(span)


    def setTocXhtml_hO(self, a, playOrder, deep, ns):
        span = etree.Element("span")
        text = a.text
        a.text = None
        if not text:
            text = a.find("{}span".format(ns)).text
        href = a.attrib.get("href").split("#")[0]
        # 除了一级标题外  href需加锚点
        a.set("href", href+"#a{}".format(playOrder.zfill(self.bit)))
        if a.getchildren():
            span = a.getchildren()[0]
            span.set("id", "t{}".format(playOrder.zfill(self.bit)))
        else:
            span.set("id", "t{}".format(playOrder.zfill(self.bit)))
            span.text = text
            a.append(span)


    # 处理除了toc.xhtml以外， TEXT 中其他的文件
    def processChapetrXhtml(self,id, html):
        print("正在处理：{}...".format(id))
        xml, ns = self.getXml(html)
        aListFromToc = self.navDic.get(id, None)
        baseIndex = 0
        refDeep = 1
        if aListFromToc:
            for h in aListFromToc:
                deep = int(h.get("deep"))
                if deep == refDeep:
                    pass
                else:
                    baseIndex = 0
                    refDeep = deep
                title = h.get("title")
                playOrder = h.get("playOrder")
                aListFromChapter = xml.findall("{0}body//{0}h{1}".format(ns, deep))
                if aListFromChapter:
                    h = aListFromChapter[baseIndex]
                    baseIndex += 1
                    self.setChapterXhtml_h(id, h, playOrder, title, deep)
        html = etree.tostring(xml, encoding="utf-8").decode("utf-8")
        return html

    def setChapterXhtml_h(self,id, h, playOrder, title, deep):
        a = etree.Element("a")
        text = h.text
        h.text = None
        if not text:
            text = title
        h.set("id", "a{}".format(playOrder.zfill(self.bit)))
        if h.getchildren():
            a = h.getchildren()[0]
            a.set("href", "../Text/toc.xhtml#t{}".format(playOrder.zfill(self.bit)))
        else:
            a.set("href", "../Text/toc.xhtml#t{}".format(playOrder.zfill(self.bit)))
            a.text = text
            h.append(a)


    # 此处有一个问题 文件的 <html xmlns="http://www...> 中的内容在自动生成xhtlm文件的时候
    # 可能会有部分属性缺失的情况，看需不需要特殊处理
    def processText(self):
        self.navDic, self.playOrder2DeepDic = self.getTocInfo()
        if self.isProcess():
            for id, href in self.bk.text_iter():
                html = self.bk.readfile(id)
                html_original = html
                if id == "toc.xhtml":
                    html = self.processTocXhtml(html)
                    print("toc.xhtml 处理完成...")
                else:
                    html = self.processChapetrXhtml(id, html)
                if not html == html_original:
                    self.bk.writefile(id, html)
            print("Text目录中文件已处理完毕...")
        else:
            print("Text目录中文件未做任何处理...")
        print("程序已退出！")




def run(bk):

    # # 处理内容
    jd = Jump2directory(bk)
    # jd.getTocInfo()
    jd.processText()
    jd.processNcx()


    return 0

def main():
    print("I reached main when I should not have\n")
    return -1

if __name__ == "__main__":
    sys.exit(main())