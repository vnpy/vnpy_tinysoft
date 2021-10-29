# vn.py框架的天软数据服务接口

<p align="center">
  <img src ="https://vnpy.oss-cn-shanghai.aliyuncs.com/vnpy-logo.png"/>
</p>

<p align="center">
    <img src ="https://img.shields.io/badge/version-2021.6.17.1-blueviolet.svg"/>
    <img src ="https://img.shields.io/badge/platform-windows|linux-yellow.svg"/>
    <img src ="https://img.shields.io/badge/python-3.7-blue.svg" />
    <img src ="https://img.shields.io/github/license/vnpy/vnpy.svg?color=orange"/>
</p>

## 说明

基于天软pyTSL接口的2021.6.17版本开发，支持以下中国金融市场的K线和Tick数据：

* 期货和期货期权：
  * CFFEX：中国金融期货交易所
  * SHFE：上海期货交易所
  * DCE：大连商品交易所
  * CZCE：郑州商品交易所
  * INE：上海国际能源交易中心
* 股票和ETF期权：
  * SSE：上海证券交易所
  * SZSE：深圳证券交易所

注意：需要购买相应的数据服务权限，可以通过[该页面](http://www.tinysoft.com.cn/TSDN/HomePage.tsl)申请试用。

安装包中集成了以下版本的pyTSL：

* Windows 64位 Python 3.7
* Ubuntu 64位 Python 3.8

如需使用其他版本，请在[天软pyTSL接口](http://www.tinysoft.com.cn/tsdn/helpdoc/display.tsl?id=17395)下载。

## 安装

安装需要基于2.7.0版本以上的[VN Studio](https://www.vnpy.com)。

直接使用pip命令：

```
pip install vnpy_tinysoft
```


或者下载解压后在cmd中运行：

```
python setup.py install
```
